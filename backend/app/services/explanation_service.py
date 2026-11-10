"""Model-specific feature explanations for triage predictions."""

from typing import Any, Dict
import re
import os
import joblib
import numpy as np
from sqlalchemy.orm import Session

from ..models import Explanation
from ml.preprocessing.cleaner import clean_text


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),  # legacy location
]


def _load_model(model_name: str):
    for directory in MODEL_DIRS:
        path = os.path.join(directory, f"{model_name}.pkl")
        if os.path.exists(path):
            return joblib.load(path)
    return None


def _class_feature_weights(classifier, target_class, features=None):
    """Return class-specific feature weights and describe their meaning."""
    if hasattr(classifier, "feature_log_prob_"):
        class_index = list(classifier.classes_).index(target_class)
        if features is not None:
            class_log_probabilities = classifier.predict_log_proba(features)[0]
            alternatives = class_log_probabilities.copy()
            alternatives[class_index] = -np.inf
            alternative_index = int(np.argmax(alternatives))
            weights = classifier.feature_log_prob_[class_index] - classifier.feature_log_prob_[alternative_index]
            return weights, "TF-IDF × MultinomialNB log-probability contrast"
        return classifier.feature_log_prob_[class_index], "TF-IDF × MultinomialNB class log-probability"

    if hasattr(classifier, "coef_"):
        class_index = list(classifier.classes_).index(target_class)
        if classifier.coef_.shape[0] == 1 and len(classifier.classes_) == 2:
            direction = 1 if class_index == 1 else -1
            return classifier.coef_[0] * direction, "TF-IDF × Logistic Regression coefficient"
        return classifier.coef_[class_index], "TF-IDF × Logistic Regression coefficient"

    # CalibratedClassifierCV retains one fitted LinearSVC per calibration fold.
    calibrated = getattr(classifier, "calibrated_classifiers_", [])
    coefficients = []
    for fitted in calibrated:
        estimator = fitted.estimator
        if hasattr(estimator, "coef_") and target_class in estimator.classes_:
            class_index = list(estimator.classes_).index(target_class)
            if estimator.coef_.shape[0] == 1 and len(estimator.classes_) == 2:
                direction = 1 if class_index == 1 else -1
                coefficients.append(estimator.coef_[0] * direction)
            else:
                coefficients.append(estimator.coef_[class_index])
    if coefficients:
        return np.mean(coefficients, axis=0), "TF-IDF × mean calibrated SVM fold coefficient"
    return None, None


def explain_with_model(text: str, model, model_name: str = "svm") -> Dict[str, Any]:
    """Return per-feature contributions for a fitted classical text model."""
    if model_name in {"cnn", "bert", "distilbert"}:
        return {
            "method": "unavailable",
            "top_features": [],
            "reason": "Neural explanations require the active model and probability scorer.",
        }

    vectorizer = model.named_steps.get("tfidf") or model.named_steps.get("vectorizer")
    classifier = model.named_steps.get("clf") or model.named_steps.get("classifier")
    if vectorizer is None or classifier is None:
        return {"method": "unavailable", "top_features": [], "reason": "Model has no supported feature-weight interface."}

    cleaned = clean_text(text)
    target_class = model.predict([cleaned])[0]
    features = vectorizer.transform([cleaned])
    coefficients, method = _class_feature_weights(classifier, target_class, features=features)
    if coefficients is None:
        return {"method": "unavailable", "top_features": [], "reason": "Model has no supported feature-weight interface."}

    contributions = features.multiply(coefficients).toarray().ravel()
    names = vectorizer.get_feature_names_out()
    indices = np.argsort(contributions)[::-1]

    def features_for(indices, word_only=False):
        output = []
        seen = set()
        for index in indices:
            name = str(names[index])
            is_word_feature = name.startswith("word__") or "__" not in name
            if contributions[index] == 0 or (contributions[index] < 0 and not word_only):
                continue
            if word_only and not is_word_feature:
                continue
            term = name.split("__", 1)[1] if "__" in name else name
            if term in seen:
                continue
            seen.add(term)
            feature_type = name.split("__", 1)[0] if "__" in name else "word"
            output.append({"term": term, "impact": float(contributions[index]), "feature": feature_type})
            if len(output) == 10:
                break
        return output

    return {
        "method": method,
        "target_class": str(target_class),
        "top_features": features_for(indices),
        "top_word_features": features_for(indices, word_only=True),
    }


def explain_neural_with_scorer(
    text: str,
    probability_scorer,
    class_labels,
    top_k: int = 10,
) -> Dict[str, Any]:
    """Explain a neural prediction by leave-one-word-out probability changes."""
    cleaned = clean_text(text)
    words = []
    for word in re.findall(r"(?u)\b\w+\b", cleaned):
        if word not in words:
            words.append(word)
    deletions = []
    for word in words:
        deleted = re.sub(rf"(?<!\w){re.escape(word)}(?!\w)", " ", cleaned, flags=re.IGNORECASE)
        deleted = re.sub(r"\s+", " ", deleted).strip()
        if deleted != cleaned:
            deletions.append((word, deleted))
    scored = np.asarray(probability_scorer([cleaned] + [deleted for _, deleted in deletions]), dtype=float)
    if scored.ndim == 1:
        scored = scored.reshape(1, -1)
    probabilities = scored[0]
    if probabilities.ndim != 1 or not len(probabilities):
        return {"method": "unavailable", "top_features": [], "reason": "Model returned no class probabilities."}
    target_index = int(np.argmax(probabilities))
    labels = list(class_labels)
    target_class = str(labels[target_index]) if target_index < len(labels) else str(target_index)

    features = []
    for index, (word, _) in enumerate(deletions, start=1):
        changed_probabilities = scored[index]
        if target_index >= len(changed_probabilities):
            continue
        features.append({
            "term": word,
            "impact": float(probabilities[target_index] - changed_probabilities[target_index]),
            "feature": "word",
        })

    features.sort(key=lambda item: abs(item["impact"]), reverse=True)
    if not features:
        return {"method": "unavailable", "top_features": [], "reason": "No words could be evaluated by deletion."}
    method = "Leave-one-word-out target-class probability change"
    top_features = features[:top_k]
    return {
        "method": method,
        "target_class": target_class,
        "top_features": top_features,
        "top_word_features": [item for item in features if item["impact"] > 0][:top_k],
    }


def generate_explanation(text: str, model_name: str = "svm") -> Dict[str, Any]:
    """Load a supported model and return its feature-level explanation."""
    if model_name in {"cnn", "bert", "distilbert"}:
        from .classification_service import _load_label_encoder, _load_model, _neural_probabilities

        normalized_name = "bert" if model_name == "distilbert" else model_name
        try:
            neural_model = _load_model(normalized_name)
            label_encoder = _load_label_encoder()
            if label_encoder is not None:
                class_labels = list(label_encoder.classes_)
            elif normalized_name == "bert":
                id2label = neural_model["model"].config.id2label
                class_labels = [id2label[index] for index in sorted(id2label)]
            else:
                class_labels = [str(index) for index in range(int(neural_model["model"].output_shape[-1]))]
            return explain_neural_with_scorer(
                text,
                lambda candidate: _neural_probabilities(neural_model, candidate, normalized_name),
                class_labels,
            )
        except (FileNotFoundError, ImportError) as error:
            return {"method": "unavailable", "top_features": [], "reason": str(error)}
    model = _load_model(model_name)
    if model is None:
        return {"method": "unavailable", "top_features": [], "reason": "Model artifact not found."}
    return explain_with_model(text, model, model_name=model_name)


def save_explanations(db: Session, evidence_id: int, model_name: str, model_version: str, explanation_data: Dict[str, Any]):
    db.query(Explanation).filter(Explanation.evidence_id == evidence_id).delete()
    for feature in explanation_data.get("top_features", []):
        db.add(Explanation(
            evidence_id=evidence_id,
            model_name=model_name,
            model_version=model_version,
            explanation_method=explanation_data.get("method", "Linear feature contribution"),
            feature_name=feature["term"],
            contribution=feature["impact"],
        ))
    db.commit()


def get_explanations(db: Session, evidence_id: int):
    return db.query(Explanation).filter(Explanation.evidence_id == evidence_id).order_by(Explanation.contribution.desc()).all()
