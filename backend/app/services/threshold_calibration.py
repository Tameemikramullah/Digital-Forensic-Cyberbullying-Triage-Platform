import os
import joblib
import numpy as np
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from ..models import Evidence, ExaminerReview, ClassificationResult
from ..config import settings
from ml.preprocessing.cleaner import clean_text


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),  # legacy location
]
LABEL_ENCODER_PATH = os.path.join(PROJECT_ROOT, "ml", "saved_models", "label_encoder.pkl")


def _load_model(model_name: str):
    for directory in MODEL_DIRS:
        path = os.path.join(directory, f"{model_name}.pkl")
        if os.path.exists(path):
            return joblib.load(path)
    raise FileNotFoundError(f"Model {model_name} not found in {MODEL_DIRS}")


def _load_label_encoder():
    for directory in MODEL_DIRS:
        path = os.path.join(directory, "label_encoder.pkl")
        if os.path.exists(path):
            return joblib.load(path)
    return None


def _get_positive_class_probability(model, text: str, label_encoder=None) -> float:
    cleaned = clean_text(text)
    proba = model.predict_proba([cleaned])[0]
    if label_encoder is not None:
        try:
            classes = label_encoder.classes_
            harmful_indices = [idx for idx, cls in enumerate(classes) if cls != "not_cyberbullying"]
            if harmful_indices:
                return float(np.sum(proba[harmful_indices]))
        except Exception:
            pass
    return float(proba.max())


def _compute_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    return float(np.mean((y_prob - y_true) ** 2))


def _compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total = len(y_true)
    for i in range(n_bins):
        mask = (y_prob > bins[i]) & (y_prob <= bins[i + 1])
        if i == 0:
            mask = (y_prob >= bins[i]) & (y_prob <= bins[i + 1])
        bin_size = float(np.sum(mask))
        if bin_size > 0:
            bin_accuracy = float(np.mean(y_true[mask]))
            bin_confidence = float(np.mean(y_prob[mask]))
            ece += (bin_size / total) * abs(bin_accuracy - bin_confidence)
    return float(ece)


def _compute_reliability_data(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> List[Dict]:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    reliability = []
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob <= bins[i + 1])
        if i == 0:
            mask = (y_prob >= bins[i]) & (y_prob <= bins[i + 1])
        bin_size = int(np.sum(mask))
        if bin_size > 0:
            bin_accuracy = float(np.mean(y_true[mask]))
            bin_confidence = float(np.mean(y_prob[mask]))
        else:
            bin_accuracy = 0.0
            bin_confidence = round(float((bins[i] + bins[i + 1]) / 2), 4)
        reliability.append({
            "bin": f"{bins[i]:.1f}-{bins[i + 1]:.1f}",
            "bin_mid": round(float((bins[i] + bins[i + 1]) / 2), 4),
            "bin_accuracy": round(bin_accuracy, 4),
            "bin_confidence": round(bin_confidence, 4),
            "bin_count": bin_size,
        })
    return reliability


def run_threshold_calibration(model_name: str = "svm", thresholds: List[float] = None, db: Session = None) -> Dict:
    if thresholds is None:
        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

    model = _load_model(model_name)
    label_encoder = _load_label_encoder()

    close_db = False
    if db is None:
        from ..database import SessionLocal
        db = SessionLocal()
        close_db = True

    try:
        reviewed = (
            db.query(Evidence, ExaminerReview)
            .join(ExaminerReview, Evidence.id == ExaminerReview.evidence_id)
            .filter(ExaminerReview.decision.in_(["CONFIRMED", "REJECTED"]))
            .all()
        )
    finally:
        if close_db:
            db.close()

    if not reviewed:
        return {
            "model_name": model_name,
            "thresholds": [],
            "message": "No reviewed evidence with ground truth available.",
        }

    y_true = []
    y_prob = []

    for evidence, review in reviewed:
        y_true.append(1 if review.decision == "CONFIRMED" else 0)
        prob = _get_positive_class_probability(model, evidence.content, label_encoder)
        y_prob.append(prob)

    y_true = np.array(y_true)
    y_prob = np.array(y_prob)

    from sklearn.metrics import recall_score, precision_score

    results = []
    total = len(y_true)
    brier_score = _compute_brier_score(y_true, y_prob)
    ece = _compute_ece(y_true, y_prob)
    actual_harmful = int(np.sum(y_true))
    reliability_data = _compute_reliability_data(y_true, y_prob)

    for threshold in thresholds:
        y_pred = (y_prob >= threshold).astype(int)
        tp = int(np.sum((y_pred == 1) & (y_true == 1)))
        fp = int(np.sum((y_pred == 1) & (y_true == 0)))
        fn = int(np.sum((y_pred == 0) & (y_true == 1)))
        tn = int(np.sum((y_pred == 0) & (y_true == 0)))

        recall = recall_score(y_true, y_pred, zero_division=0)
        precision = precision_score(y_true, y_pred, zero_division=0)
        flagged = tp + fp
        workload_reduction = ((total - flagged) / total * 100) if total > 0 else 0.0
        missed_evidence_rate = (fn / actual_harmful * 100) if actual_harmful > 0 else 0.0

        results.append({
            "threshold": threshold,
            "recall": round(float(recall) * 100, 2),
            "precision": round(float(precision) * 100, 2),
            "workload_reduction": round(float(workload_reduction), 2),
            "missed_evidence_rate": round(float(missed_evidence_rate), 2),
            "brier_score": round(brier_score, 4),
            "ece": round(ece, 4),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "flagged_count": flagged,
            "total_reviewed": total,
        })

    best = max(results, key=lambda r: (r["precision"] + r["recall"]) / 2) if results else None

    return {
        "model_name": model_name,
        "total_reviewed": total,
        "actual_harmful": actual_harmful,
        "brier_score": round(brier_score, 4),
        "ece": round(ece, 4),
        "selected_threshold": best["threshold"] if best else 0.7,
        "results": results,
        "reliability_data": reliability_data,
    }
