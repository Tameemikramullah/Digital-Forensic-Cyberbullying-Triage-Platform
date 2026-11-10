import os
import joblib
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Evidence, ClassificationResult, ExaminerReview
from ml.preprocessing.cleaner import clean_text
from ml.operational.simulated_cases import SIMULATED_CASES


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),
]
CANONICAL_LABELS = {"age", "ethnicity", "gender", "not_cyberbullying", "other_cyberbullying", "religion"}


def _load_model(model_name: str = "svm"):
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


def _harmful_probability(model, cleaned: str) -> float:
    """Probability used by the deployed harmful-vs-benign triage decision."""
    probabilities = model.predict_proba([cleaned])[0]
    classes = [str(label) for label in model.classes_]
    harmful_indices = [index for index, label in enumerate(classes) if label != "not_cyberbullying"]
    return float(np.sum(probabilities[harmful_indices])) if harmful_indices else 0.0


def _wilson_interval(successes: int, total: int, z: float = 1.96):
    if total <= 0:
        return None
    rate = successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    margin = z * np.sqrt((rate * (1 - rate) + z * z / (4 * total)) / total) / denominator
    return [round(max(0.0, center - margin) * 100, 2), round(min(1.0, center + margin) * 100, 2)]


def _latest_classification(db: Session, evidence_id: int):
    return (
        db.query(ClassificationResult)
        .filter(ClassificationResult.evidence_id == evidence_id)
        .order_by(ClassificationResult.created_at.desc())
        .first()
    )


def _latest_review(db: Session, evidence_id: int):
    return (
        db.query(ExaminerReview)
        .filter(ExaminerReview.evidence_id == evidence_id)
        .order_by(ExaminerReview.created_at.desc())
        .first()
    )


def compute_operational_metrics(db: Session) -> Dict[str, Any]:
    total_evidence = db.query(Evidence).count()
    triaged = db.query(Evidence).filter(Evidence.status.in_(["TRIAGED", "REVIEWED", "CLOSED"])).count()
    reviewed = db.query(Evidence).filter(Evidence.status == "REVIEWED").count()

    evidence_items = db.query(Evidence).all()

    y_true = []
    y_pred = []
    reviewer_account_counts: Dict[str, int] = {}
    disagreement_by_reviewer: Dict[str, int] = {}
    prediction_review_disagreements = 0
    invalid_prediction_count = 0
    flagged_set = set()
    confirmed_set = set()
    rejected_set = set()
    escalated_set = set()

    for evidence in evidence_items:
        classification = _latest_classification(db, evidence.id)
        review = _latest_review(db, evidence.id)

        if not classification or not review:
            continue

        if review.decision == "CONFIRMED":
            confirmed_set.add(evidence.id)
        elif review.decision == "REJECTED":
            rejected_set.add(evidence.id)
        elif review.decision == "NEEDS_MORE_REVIEW":
            escalated_set.add(evidence.id)

        if classification.prediction not in CANONICAL_LABELS:
            invalid_prediction_count += 1
            continue

        if classification.prediction != "not_cyberbullying":
            flagged_set.add(evidence.id)

        if review.decision in ["CONFIRMED", "REJECTED"]:
            reference = 1 if review.decision == "CONFIRMED" else 0
            predicted = 1 if classification.prediction != "not_cyberbullying" else 0
            y_true.append(reference)
            y_pred.append(predicted)
            reviewer_id = str(review.examiner_id)
            reviewer_account_counts[reviewer_id] = reviewer_account_counts.get(reviewer_id, 0) + 1
            if reference != predicted:
                prediction_review_disagreements += 1
                disagreement_by_reviewer[reviewer_id] = disagreement_by_reviewer.get(reviewer_id, 0) + 1

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))

    total_paired = len(y_true)
    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
    fpr = (fp / (fp + tn) * 100) if (fp + tn) > 0 else 0.0
    fnr = (fn / (tp + fn) * 100) if (tp + fn) > 0 else 0.0

    flagged = len(flagged_set)
    workload_reduction = ((total_evidence - flagged) / total_evidence * 100) if total_evidence > 0 else 0.0
    triage_reduction = ((total_evidence - triaged) / total_evidence * 100) if total_evidence > 0 else 0.0

    return {
        "total_evidence": total_evidence,
        "triaged": triaged,
        "reviewed": reviewed,
        "flagged": flagged,
        "confirmed": len(confirmed_set),
        "rejected": len(rejected_set),
        "escalated": len(escalated_set),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "total_paired": total_paired,
        "accuracy": round(((tp + tn) / total_paired * 100) if total_paired else 0.0, 2),
        "prediction_review_disagreements": prediction_review_disagreements,
        "invalid_prediction_count": invalid_prediction_count,
        "reviewer_account_counts": reviewer_account_counts,
        "disagreements_by_reviewer_account": disagreement_by_reviewer,
        "reviewer_credentials_verified": False,
        "recall": round(recall, 2),
        "precision": round(precision, 2),
        "confidence_intervals_95": {
            "accuracy": _wilson_interval(tp + tn, total_paired),
            "precision": _wilson_interval(tp, tp + fp),
            "recall": _wilson_interval(tp, tp + fn),
            "method": "Wilson score intervals (95%)",
        },
        "false_positive_rate": round(fpr, 2),
        "false_negative_rate": round(fnr, 2),
        "workload_reduction": round(workload_reduction, 2),
        "triage_reduction": round(triage_reduction, 2),
    }


def run_simulated_cases(db: Session, model_name: str = "svm") -> Dict[str, Any]:
    model = _load_model(model_name)
    label_encoder = _load_label_encoder()

    # Mirror the deployed policy. If no reviewed operational set is available,
    # use the documented default rather than changing the decision silently.
    threshold = 0.7
    try:
        from .threshold_calibration import run_threshold_calibration
        calibration = run_threshold_calibration(model_name=model_name, db=db)
        threshold = float(calibration.get("selected_threshold", threshold))
    except Exception:
        pass

    results = []
    tp = fp = fn = tn = 0

    for case in SIMULATED_CASES:
        content = case["content"]
        reference_label = case["reference_label"]

        cleaned = clean_text(content)
        prediction = str(model.predict([cleaned])[0])
        confidence = float(model.predict_proba([cleaned])[0].max())
        harmful_probability = _harmful_probability(model, cleaned)

        if label_encoder is not None:
            try:
                prediction = label_encoder.inverse_transform([int(prediction)])[0]
            except Exception:
                pass

        predicted_flagged = harmful_probability >= threshold
        actual_flagged = reference_label == "cyberbullying"

        if predicted_flagged and actual_flagged:
            tp += 1
        elif predicted_flagged and not actual_flagged:
            fp += 1
        elif not predicted_flagged and actual_flagged:
            fn += 1
        else:
            tn += 1

        results.append({
            "id": case["id"],
            "content": content,
            "category": case["category"],
            "description": case["description"],
            "reference_label": reference_label,
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "harmful_probability": round(harmful_probability, 4),
            "threshold": threshold,
            "predicted_flagged": predicted_flagged,
            "actual_flagged": actual_flagged,
            "correct": predicted_flagged == actual_flagged,
        })

    total = len(SIMULATED_CASES)
    accuracy = (tp + tn) / total * 100 if total > 0 else 0.0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0.0
    fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0.0
    fnr = fn / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "model_name": model_name,
        "evaluation_type": "CURATED_SIMULATION",
        "label_source": "Author-assigned from training-data annotation patterns; not independently adjudicated",
        "independent_validation": False,
        "independent_annotator_count": 0,
        "annotator_agreement": None,
        "threshold": threshold,
        "total_cases": total,
        "correct": tp + tn,
        "incorrect": fp + fn,
        "accuracy": round(accuracy, 2),
        "confidence_intervals_95": {
            "accuracy": _wilson_interval(tp + tn, total),
            "precision": _wilson_interval(tp, tp + fp),
            "recall": _wilson_interval(tp, tp + fn),
            "method": "Wilson score intervals (95%)",
        },
        "recall": round(recall, 2),
        "precision": round(precision, 2),
        "f1_score": round(f1, 2),
        "false_positive_rate": round(fpr, 2),
        "false_negative_rate": round(fnr, 2),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "results": results,
    }
