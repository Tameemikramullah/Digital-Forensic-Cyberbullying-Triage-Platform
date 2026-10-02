"""Deterministic explanations for the classical triage models."""

from typing import Any, Dict
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


def _linear_coefficients(classifier, target_class):
    """Return the target-class coefficients for LogisticRegression or calibrated LinearSVC."""
    if hasattr(classifier, "coef_"):
        classes = classifier.classes_
        return classifier.coef_[list(classes).index(target_class)]

    # CalibratedClassifierCV retains one fitted LinearSVC per calibration fold.
    calibrated = getattr(classifier, "calibrated_classifiers_", [])
    coefficients = []
    for fitted in calibrated:
        estimator = fitted.estimator
        if hasattr(estimator, "coef_") and target_class in estimator.classes_:
            class_index = list(estimator.classes_).index(target_class)
            coefficients.append(estimator.coef_[class_index])
    if coefficients:
        return np.mean(coefficients, axis=0)
    return None


def generate_explanation(text: str, model_name: str = "svm") -> Dict[str, Any]:
    """Return repeatable per-feature contributions for a linear prediction.

    Unlike Kernel/black-box SHAP, this uses the model's actual coefficients,
    avoiding random sampling, dense matrices and multi-second latency.
    """
    model = _load_model(model_name)
    if model is None:
        return {"method": "Linear feature contribution", "top_features": []}
    vectorizer = model.named_steps.get("tfidf") or model.named_steps.get("vectorizer")
    classifier = model.named_steps.get("clf") or model.named_steps.get("classifier")
    if vectorizer is None or classifier is None:
        return {"method": "Linear feature contribution", "top_features": []}

    cleaned = clean_text(text)
    target_class = model.predict([cleaned])[0]
    coefficients = _linear_coefficients(classifier, target_class)
    if coefficients is None:
        return {"method": "Linear feature contribution", "top_features": []}

    features = vectorizer.transform([cleaned])
    contributions = features.multiply(coefficients).toarray().ravel()
    names = vectorizer.get_feature_names_out()
    # A flagged-item explanation should show evidence *for* its predicted class.
    indices = np.argsort(contributions)[::-1]
    top_features = [
        {"term": str(names[index]), "impact": float(contributions[index])}
        for index in indices
        if contributions[index] > 0
    ][:10]
    return {"method": "Linear feature contribution", "top_features": top_features}


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
