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
    roc_auc_score,
)


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
    y_prob = []
    model_names = []
    evidence_ids = []

    for evidence, classification, review in rows:
        y_true.append(1 if review.decision == "CONFIRMED" else 0)
        y_pred.append(1 if classification.prediction != "not_cyberbullying" else 0)
        y_prob.append(float(classification.confidence_score))
        model_names.append(classification.model_name)
        evidence_ids.append(evidence.id)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_prob = np.array(y_prob)

    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        roc_auc = 0.0

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel().tolist()

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    unique_models = sorted(set(model_names))
    model_counts = {m: model_names.count(m) for m in unique_models}

    return {
        "model_name": model_name or "all",
        "total_evaluated": len(y_true),
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1": round(f1 * 100, 2),
        "roc_auc": round(roc_auc * 100, 2),
        "false_positive_rate": round(fpr * 100, 2),
        "false_negative_rate": round(fnr * 100, 2),
        "confusion_matrix": {"tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)},
        "model_distribution": model_counts,
        "evidence_ids": evidence_ids,
    }
