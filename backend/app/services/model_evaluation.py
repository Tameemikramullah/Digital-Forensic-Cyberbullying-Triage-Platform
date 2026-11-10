from sqlalchemy.orm import Session
from ..models import Evidence, ClassificationResult, ExaminerReview
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

CANONICAL_LABELS = {"age", "ethnicity", "gender", "not_cyberbullying", "other_cyberbullying", "religion"}


def _wilson_interval(successes: int, total: int, z: float = 1.96):
    if total <= 0:
        return None
    rate = successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    margin = z * np.sqrt((rate * (1 - rate) + z * z / (4 * total)) / total) / denominator
    return [round(max(0.0, center - margin) * 100, 2), round(min(1.0, center + margin) * 100, 2)]


def compute_model_evaluation(db: Session, model_name: str = None) -> Dict[str, Any]:
    query = (
        db.query(Evidence, ClassificationResult, ExaminerReview)
        .join(ClassificationResult, Evidence.id == ClassificationResult.evidence_id)
        .join(ExaminerReview, Evidence.id == ExaminerReview.evidence_id)
        .filter(ExaminerReview.decision.in_(["CONFIRMED", "REJECTED"]))
    )

    if model_name:
        query = query.filter(ClassificationResult.model_name == model_name)

    rows = query.all()

    if not rows:
        return {
            "model_name": model_name or "all",
            "total_evaluated": 0,
            "message": "No reviewed evidence with model predictions available.",
        }

    y_true = []
    y_pred = []
    model_names = []
    evidence_ids = []
    invalid_prediction_count = 0

    for evidence, classification, review in rows:
        if classification.prediction not in CANONICAL_LABELS:
            invalid_prediction_count += 1
            continue
        y_true.append(1 if review.decision == "CONFIRMED" else 0)
        y_pred.append(1 if classification.prediction != "not_cyberbullying" else 0)
        model_names.append(classification.model_name)
        evidence_ids.append(evidence.id)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    if len(y_true) == 0:
        return {
            "model_name": model_name or "all",
            "total_evaluated": 0,
            "invalid_prediction_count": invalid_prediction_count,
            "message": "No compatible canonical-label predictions are available for the reviewed evidence.",
        }

    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    # ClassificationResult stores top-class confidence, not harmful-class probability.
    # ROC-AUC is intentionally unavailable from this table alone.

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel().tolist()

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    unique_models = sorted(set(model_names))
    model_counts = {m: model_names.count(m) for m in unique_models}

    return {
        "model_name": model_name or "all",
        "total_evaluated": len(y_true),
        "invalid_prediction_count": invalid_prediction_count,
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1": round(f1 * 100, 2),
        "roc_auc": None,
        "roc_auc_note": "Not computed: stored confidence is top-class confidence, not harmful-class probability.",
        "false_positive_rate": round(fpr * 100, 2),
        "false_negative_rate": round(fnr * 100, 2),
        "confusion_matrix": {"tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)},
        "confidence_intervals_95": {
            "accuracy": _wilson_interval(tp + tn, len(y_true)),
            "precision": _wilson_interval(tp, tp + fp),
            "recall": _wilson_interval(tp, tp + fn),
            "method": "Wilson score intervals (95%)",
        },
        "model_distribution": model_counts,
        "evidence_ids": evidence_ids,
    }
