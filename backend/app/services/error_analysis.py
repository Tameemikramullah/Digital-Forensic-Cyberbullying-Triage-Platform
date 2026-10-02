from sqlalchemy.orm import Session
from ..models import Evidence, ClassificationResult, ExaminerReview
from typing import Dict, Any, List
import numpy as np
from .error_categorization import categorize_error


def _latest_classification(db: Session, evidence_id: int) -> ClassificationResult | None:
    return (
        db.query(ClassificationResult)
        .filter(ClassificationResult.evidence_id == evidence_id)
        .order_by(ClassificationResult.created_at.desc())
        .first()
    )


def _latest_review(db: Session, evidence_id: int) -> ExaminerReview | None:
    return (
        db.query(ExaminerReview)
        .filter(ExaminerReview.evidence_id == evidence_id)
        .order_by(ExaminerReview.created_at.desc())
        .first()
    )


def compute_error_analysis(db: Session) -> Dict[str, Any]:
    evidence_items = db.query(Evidence).all()

    false_positives: List[Dict[str, Any]] = []
    false_negatives: List[Dict[str, Any]] = []
    ambiguous_cases: List[Dict[str, Any]] = []
    true_positives = 0
    true_negatives = 0

    category_counts: Dict[str, int] = {}
    category_details: Dict[str, List[Dict[str, Any]]] = {}

    y_true = []
    y_pred = []

    for evidence in evidence_items:
        classification = _latest_classification(db, evidence.id)
        review = _latest_review(db, evidence.id)

        if not classification or not review:
            continue

        prediction = classification.prediction
        confidence = float(classification.confidence_score)
        decision = review.decision
        review_notes = review.notes

        row = {
            "evidence_id": evidence.id,
            "source_platform": evidence.source_platform,
            "content": evidence.content,
            "prediction": prediction,
            "confidence": confidence,
            "examiner_decision": decision,
            "review_notes": review_notes,
            "model_name": classification.model_name,
            "model_version": classification.model_version,
            "threshold": classification.threshold,
            "risk_level": classification.risk_level,
        }

        predicted_flagged = prediction != "not_cyberbullying"
        ground_truth_harmful = decision == "CONFIRMED"

        y_true.append(1 if ground_truth_harmful else 0)
        y_pred.append(1 if predicted_flagged else 0)

        is_false_positive = predicted_flagged and not ground_truth_harmful
        is_false_negative = not predicted_flagged and ground_truth_harmful
        is_ambiguous = confidence < 0.75 or decision == "NEEDS_MORE_REVIEW"

        if is_false_positive:
            false_positives.append(row)
        elif is_false_negative:
            false_negatives.append(row)
        elif is_ambiguous:
            ambiguous_cases.append(row)

        if predicted_flagged and ground_truth_harmful:
            true_positives += 1
        if not predicted_flagged and not ground_truth_harmful:
            true_negatives += 1

        error_type = None
        if is_false_positive:
            error_type = "FALSE_POSITIVE"
        elif is_false_negative:
            error_type = "FALSE_NEGATIVE"
        elif is_ambiguous:
            error_type = "AMBIGUOUS"

        if error_type:
            categories = categorize_error(review_notes, evidence.content, prediction, decision)
            row["error_categories"] = categories
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1
                if category not in category_details:
                    category_details[category] = []
                category_details[category].append({
                    "evidence_id": evidence.id,
                    "error_type": error_type,
                    "content": evidence.content,
                    "prediction": prediction,
                    "examiner_decision": decision,
                    "review_notes": review_notes,
                })

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    total_paired = len(y_true)
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))

    total_evaluated = len(false_positives) + len(false_negatives) + len(ambiguous_cases) + true_positives + true_negatives
    total_errors = len(false_positives) + len(false_negatives)
    error_rate = (total_errors / total_evaluated * 100) if total_evaluated > 0 else 0.0

    discussion = {
        "total_evaluated": total_evaluated,
        "total_paired": total_paired,
        "true_positives": true_positives,
        "true_negatives": true_negatives,
        "false_positives_count": len(false_positives),
        "false_negatives_count": len(false_negatives),
        "ambiguous_count": len(ambiguous_cases),
        "error_rate": round(error_rate, 2),
        "false_positive_rate": round((fp / total_paired * 100) if total_paired > 0 else 0.0, 2),
        "false_negative_rate": round((fn / total_paired * 100) if total_paired > 0 else 0.0, 2),
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "category_counts": category_counts,
        "category_details": category_details,
    }

    return {
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "ambiguous_cases": ambiguous_cases,
        "discussion": discussion,
    }
