import os
import time
import joblib
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sklearn.metrics import f1_score, roc_auc_score
from ..models import Evidence, ExaminerReview
from ml.preprocessing.cleaner import clean_text
from ml.preprocessing.tokenizer import pad_sequences

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),  # legacy location
]

EXPLAINABILITY_SCORES = {
    "svm": "High",
    "logistic": "High",
    "naive_bayes": "Medium",
    "cnn": "Medium",
    "bert": "Lower",
}

RUNTIME_CLASSES = {
    "svm": "Fast",
    "logistic": "Fast",
    "naive_bayes": "Fast",
    "cnn": "Medium",
    "bert": "Slow",
}


def _load_model(model_name: str):
    for directory in MODEL_DIRS:
        if model_name in ["svm", "logistic", "naive_bayes"]:
            path = os.path.join(directory, f"{model_name}.pkl")
            if os.path.exists(path):
                return joblib.load(path)
        elif model_name == "cnn":
            model_path = os.path.join(directory, "cnn_model.keras")
            if os.path.exists(model_path):
                import tensorflow as tf
                from ml.preprocessing.tokenizer import load_tokenizer
                tokenizer_path = os.path.join(directory, "cnn_tokenizer.json")
                if not os.path.exists(tokenizer_path):
                    continue
                tokenizer, _ = load_tokenizer(tokenizer_path)
                return {"type": "cnn", "model": tf.keras.models.load_model(model_path), "tokenizer": tokenizer}
        elif model_name == "bert":
            model_path = os.path.join(directory, "bert_model")
            if os.path.exists(model_path):
                os.environ["CUDA_VISIBLE_DEVICES"] = ""
                import torch
                torch.set_num_threads(4)
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSequenceClassification.from_pretrained(model_path)
                model = model.to("cpu").eval()
                return {"type": "bert", "model": model, "tokenizer": tokenizer}
    return None


def _load_label_encoder():
    for directory in MODEL_DIRS:
        path = os.path.join(directory, "label_encoder.pkl")
        if os.path.exists(path):
            return joblib.load(path)
    return None


def _get_evidence_with_reviews(db: Session) -> List[tuple]:
    return (
        db.query(Evidence, ExaminerReview)
        .join(ExaminerReview, Evidence.id == ExaminerReview.evidence_id)
        .filter(ExaminerReview.decision.in_(["CONFIRMED", "REJECTED"]))
        .all()
    )


def _decode_labels(values) -> List[str]:
    labels = [str(value) for value in values]
    encoder = _load_label_encoder()
    encoded = all(label.isdigit() or (label.startswith("LABEL_") and label[6:].isdigit()) for label in labels)
    if encoder is not None and encoded:
        indices = [int(label if label.isdigit() else label[6:]) for label in labels]
        labels = [str(value) for value in encoder.inverse_transform(indices)]
    return labels


def _harmful_probability(labels: List[str], probabilities: np.ndarray) -> float:
    if len(labels) != len(probabilities):
        raise RuntimeError("Class labels do not match model probability outputs")
    if "not_cyberbullying" not in labels:
        raise RuntimeError("Model output is missing the canonical benign class mapping")
    return float(sum(probability for label, probability in zip(labels, probabilities) if label != "not_cyberbullying"))


def _predict(model, text: str, model_name: str = "") -> tuple:
    cleaned = clean_text(text)
    if model_name == "cnn" and isinstance(model, dict):
        sequences = model["tokenizer"].texts_to_sequences([cleaned])
        padded = pad_sequences(sequences, maxlen=200, padding="post", truncating="post")
        probabilities = np.asarray(model["model"].predict(padded, verbose=0)[0], dtype=float)
        class_index = int(np.argmax(probabilities))
        encoder = _load_label_encoder()
        if encoder is None or len(probabilities) != len(encoder.classes_):
            raise RuntimeError("CNN artifact uses an obsolete label space; retrain it on the current six-class task")
        labels = [str(label) for label in encoder.classes_]
        predicted_label = labels[class_index]
        return int(predicted_label != "not_cyberbullying"), _harmful_probability(labels, probabilities)
    if model_name == "bert" and isinstance(model, dict):
        import torch
        inputs = model["tokenizer"]([cleaned], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            logits = model["model"](**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=1).numpy()[0]
        encoder = _load_label_encoder()
        if encoder is not None and len(probs) != len(encoder.classes_):
            raise RuntimeError("DistilBERT artifact uses an obsolete label space; retrain it on the current six-class task")
        pred = int(np.argmax(probs))
        raw_labels = [model["model"].config.id2label.get(i, f"LABEL_{i}") for i in range(len(probs))]
        labels = _decode_labels(raw_labels)
        return int(labels[pred] != "not_cyberbullying"), _harmful_probability(labels, probs)
    probabilities = np.asarray(model.predict_proba([cleaned])[0], dtype=float)
    labels = _decode_labels(model.classes_)
    prediction = model.predict([cleaned])[0]
    predicted_label = _decode_labels([prediction])[0]
    return int(predicted_label != "not_cyberbullying"), _harmful_probability(labels, probabilities)


def _wilson_interval(successes: int, total: int, z: float = 1.96):
    if total <= 0:
        return None
    rate = successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    margin = z * np.sqrt((rate * (1 - rate) + z * z / (4 * total)) / total) / denominator
    return [round(max(0.0, center - margin) * 100, 2), round(min(1.0, center + margin) * 100, 2)]


def _bootstrap_f1_interval(y_true: np.ndarray, y_pred: np.ndarray, seed: int = 42, samples: int = 2000):
    if len(y_true) == 0:
        return None
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(samples):
        indices = rng.integers(0, len(y_true), len(y_true))
        scores.append(float(f1_score(y_true[indices], y_pred[indices], zero_division=0)))
    return [round(float(np.percentile(scores, 2.5)) * 100, 2), round(float(np.percentile(scores, 97.5)) * 100, 2)]


def run_inter_model_comparison(db: Session, model_names: List[str] = None) -> Dict[str, Any]:
    if model_names is None:
        model_names = ["svm", "logistic", "naive_bayes", "cnn", "bert"]

    evidence_reviews = _get_evidence_with_reviews(db)

    if not evidence_reviews:
        return {
            "models": [],
            "message": "No reviewed evidence available for comparison.",
        }

    y_true = []
    texts = []
    for evidence, review in evidence_reviews:
        y_true.append(1 if review.decision == "CONFIRMED" else 0)
        texts.append(evidence.content)

    y_true = np.array(y_true)
    total_pairs = len(y_true)
    reviewer_counts: Dict[str, int] = {}
    for _, review in evidence_reviews:
        reviewer_id = str(review.examiner_id)
        reviewer_counts[reviewer_id] = reviewer_counts.get(reviewer_id, 0) + 1

    MIN_SAMPLE_SIZE = 10
    small_sample_warning = total_pairs < MIN_SAMPLE_SIZE
    perfect_score_warning = False

    results = []

    for model_name in model_names:
        try:
            model = _load_model(model_name)
        except Exception as exc:
            results.append({
                "model": model_name,
                "f1": None,
                "runtime": RUNTIME_CLASSES.get(model_name, "Unknown"),
                "explainability": EXPLAINABILITY_SCORES.get(model_name, "Unknown"),
                "selected": False,
                "error": f"Model could not be loaded: {exc}",
                "warning": None,
                "evaluated_pairs": 0,
            })
            continue
        if model is None:
            artifact_error = "No trained compatible model artifact found"
            if model_name in ["cnn", "bert"]:
                artifact_error = "TensorFlow is not installed in the backend environment; CNN/DistilBERT artifacts cannot be loaded or compared"
            results.append({
                "model": model_name,
                "f1": None,
                "runtime": RUNTIME_CLASSES.get(model_name, "Unknown"),
                "explainability": EXPLAINABILITY_SCORES.get(model_name, "Unknown"),
                "selected": False,
                "error": artifact_error,
                "warning": None,
            })
            continue

        start = time.time()
        y_pred = []
        y_prob = []
        y_true_model = []
        evaluated_evidence_ids = []
        evaluated_reviewer_ids = []
        inference_errors = 0
        for (evidence, review), target in zip(evidence_reviews, y_true):
            try:
                pred, probability = _predict(model, evidence.content, model_name)
                y_pred.append(pred)
                y_prob.append(probability)
                y_true_model.append(int(target))
                evaluated_evidence_ids.append(evidence.id)
                evaluated_reviewer_ids.append(review.examiner_id)
            except Exception:
                inference_errors += 1
        elapsed_ms = (time.time() - start) * 1000

        avg_runtime_ms = elapsed_ms / len(y_pred) if y_pred else 0
        runtime_class = "Fast" if avg_runtime_ms < 50 else "Medium" if avg_runtime_ms < 500 else "Slow"

        y_true_model = np.asarray(y_true_model, dtype=int)
        y_pred = np.asarray(y_pred, dtype=int)
        f1 = float(f1_score(y_true_model, y_pred, zero_division=0)) if len(y_true_model) else 0.0
        f1_pct = round(f1 * 100, 2)
        tp = int(np.sum((y_true_model == 1) & (y_pred == 1)))
        fp = int(np.sum((y_true_model == 0) & (y_pred == 1)))
        fn = int(np.sum((y_true_model == 1) & (y_pred == 0)))
        tn = int(np.sum((y_true_model == 0) & (y_pred == 0)))
        mismatch_indices = np.flatnonzero(y_true_model != y_pred)
        error_reviewers: Dict[str, int] = {}
        for index in mismatch_indices:
            reviewer_id = str(evaluated_reviewer_ids[index])
            error_reviewers[reviewer_id] = error_reviewers.get(reviewer_id, 0) + 1

        warnings = []
        if small_sample_warning:
            warnings.append(
                f"Small sample size ({len(y_true_model)} evaluated of {total_pairs} reviewed items). Operational F1 may not be statistically reliable."
            )
        if inference_errors:
            warnings.append(f"{inference_errors} inference failures were excluded from this model's denominator.")
        if f1_pct == 100.0:
            perfect_score_warning = True
            warnings.append(
                "Perfect operational F1 (100%) is suspicious. This may indicate data leakage, overfitting, or an overly trivial reviewed set."
            )

        results.append({
            "model": model_name,
            "f1": f1_pct,
            "roc_auc": round(float(roc_auc_score(y_true_model, y_prob)) * 100, 2) if len(set(y_true_model.tolist())) > 1 else None,
            "runtime": runtime_class,
            "avg_runtime_ms": round(avg_runtime_ms, 2),
            "explainability": EXPLAINABILITY_SCORES.get(model_name, "Unknown"),
            "selected": model_name == "svm" and len(y_true_model) > 0,
            "warning": " | ".join(warnings) if warnings else None,
            "evaluated_pairs": len(y_true_model),
            "inference_errors": inference_errors,
            "prediction_review_disagreements": len(mismatch_indices),
            "disagreement_evidence_ids": [evaluated_evidence_ids[i] for i in mismatch_indices],
            "disagreements_by_reviewer_account": error_reviewers,
            "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "confidence_intervals_95": {
                "accuracy": _wilson_interval(tp + tn, len(y_true_model)),
                "precision": _wilson_interval(tp, tp + fp),
                "recall": _wilson_interval(tp, tp + fn),
                "f1_bootstrap": _bootstrap_f1_interval(y_true_model, y_pred),
            },
        })

    selected = next((r for r in results if r["selected"]), None)
    justification = (
        "SVM selected for operational triage due to coefficient-based explainability, deterministic runtime, "
        "and strong held-out multiclass performance. The displayed F1 is a binary agreement score against "
        "app-recorded review decisions, not the model's held-out macro-F1."
        if selected else "No model selected."
    )

    global_warnings = []
    if small_sample_warning:
        global_warnings.append(
            f"Global warning: only {total_pairs} app-reviewed evidence items are available. "
            "Collect more independently reviewed cases before using these operational metrics for publication."
        )
    if perfect_score_warning:
        global_warnings.append(
            "Global warning: one or more models achieved 100% operational F1. "
            "Investigate possible data leakage, training/test overlap, or dataset bias before citing these results."
        )

    return {
        "models": results,
        "selected_model": selected["model"] if selected else None,
        "justification": justification,
        "warnings": global_warnings,
        "meta": {
            "total_reviewed_pairs": total_pairs,
            "small_sample_warning": small_sample_warning,
            "perfect_score_warning": perfect_score_warning,
            "reviewer_account_counts": reviewer_counts,
            "reviewer_credentials_verified": False,
            "confidence_interval_method": "Wilson 95% intervals for accuracy, precision, and recall; percentile bootstrap for F1 (2,000 resamples, seed 42)",
        },
    }
