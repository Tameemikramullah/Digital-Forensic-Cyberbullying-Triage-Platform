import json
import os
import joblib
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import Evidence, RepeatabilityTest
from ..services.classification_service import classify_text
from ..services.explanation_service import generate_explanation
from ml.preprocessing.cleaner import clean_text


def _normalize_explanation(top_features: List[Dict[str, Any]]) -> frozenset:
    return frozenset(
        (
            str(f.get("term", "")),
            round(float(f.get("impact", 0.0)), 4),
        )
        for f in (top_features or [])
    )


def run_repeatability_test(db: Session, evidence_id: int, model_name: str = "svm", iterations: int = 10) -> Dict[str, Any]:
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise ValueError("Evidence not found")

    predictions = []
    confidences = []
    explanation_signatures = []

    for _ in range(iterations):
        prediction, confidence = classify_text(evidence.content, model_name=model_name)
        explanation = generate_explanation(evidence.content, model_name=model_name)
        predictions.append(prediction)
        confidences.append(confidence)
        explanation_signatures.append(_normalize_explanation(explanation.get("top_features", [])))

    prediction_consistency = len(set(predictions)) == 1
    confidence_variance = max(confidences) - min(confidences) if len(confidences) > 1 else 0.0

    explanation_consistency = len(set(explanation_signatures)) <= 1

    prediction_consistency_pct = 100.0 if prediction_consistency else 0.0
    explanation_consistency_pct = 100.0 if explanation_consistency else 0.0
    confidence_variance_pct = confidence_variance * 100

    pass_fail = "PASS" if prediction_consistency and explanation_consistency and confidence_variance < 0.05 else "FAIL"

    result = RepeatabilityTest(
        evidence_id=evidence_id,
        model_name=model_name,
        iterations=iterations,
        prediction_consistency=prediction_consistency_pct,
        confidence_variance=confidence_variance_pct,
        explanation_consistency=explanation_consistency_pct,
        pass_fail=pass_fail,
        details_json=json.dumps({
            "predictions": predictions,
            "confidences": confidences,
            "iterations": iterations,
        }),
    )
    db.add(result)
    db.commit()

    return {
        "evidence_id": evidence_id,
        "model_name": model_name,
        "iterations": iterations,
        "prediction_consistency": prediction_consistency_pct,
        "confidence_variance": confidence_variance_pct,
        "explanation_consistency": explanation_consistency_pct,
        "pass_fail": pass_fail,
        "details": result.details_json,
    }
