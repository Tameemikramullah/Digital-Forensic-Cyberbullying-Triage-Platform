from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time
from typing import List, Dict, Any
from ..database import get_db
from ..schemas import TriageRequest, TriageResponse, EnsembleRequest, EnsembleResponse, ModelVote
from ..models import User, Evidence, EvidenceStatus, ClassificationResult
from ..security.auth import get_current_user
from ..services.classification_service import classify_text, classify_text_with_explanation
from ..services.explanation_service import generate_explanation, save_explanations
from ..services.audit_service import create_audit_log
from ..services.chain_of_custody import ChainOfCustodyTracker

router = APIRouter()


def _get_calibrated_threshold(model_name: str, db: Session) -> float:
    try:
        from ..services.threshold_calibration import run_threshold_calibration
        calibration = run_threshold_calibration(model_name=model_name, db=db)
        if calibration.get("results"):
            best = max(calibration["results"], key=lambda r: (r.get("precision", 0) + r.get("recall", 0)) / 2)
            return float(best.get("threshold", 0.7))
    except Exception:
        pass
    return 0.7


def _compute_risk(prediction: str, confidence: float, threshold: float = 0.7) -> tuple[str, bool]:
    if prediction == "not_cyberbullying" or confidence < threshold:
        return "LOW", False
    if confidence >= 0.8:
        return "HIGH", True
    if confidence >= 0.5:
        return "MEDIUM", True
    return "LOW", True


def _check_model_agreement(votes: List[dict], confidence_spread_threshold: float = 0.30) -> Dict[str, Any]:
    successful_votes = [v for v in votes if v.get("prediction") != "error"]
    if not successful_votes:
        return {"agreement": "unknown", "confidence_spread": 0.0, "disagreement_levels": 0, "unique_predictions": []}
    predictions = [v["prediction"] for v in successful_votes]
    unique_predictions = list(set(predictions))
    confidences = [v["confidence"] for v in successful_votes]
    confidence_spread = max(confidences) - min(confidences) if len(confidences) > 1 else 0.0
    agreement = "full" if len(unique_predictions) == 1 else "partial" if len(unique_predictions) == 2 else "none"
    forced_review = False
    if len(successful_votes) >= 2:
        if len(unique_predictions) > 2 or confidence_spread > confidence_spread_threshold:
            forced_review = True
    return {
        "agreement": agreement,
        "confidence_spread": round(confidence_spread, 4),
        "disagreement_levels": len(unique_predictions),
        "unique_predictions": unique_predictions,
        "forced_review": forced_review,
    }


PREPROCESSING_STEPS = "Lowercasing; URL and user-token normalisation; hashtag-word retention; punctuation normalisation"


@router.post("/{evidence_id}", response_model=TriageResponse)
def triage_evidence(evidence_id: int, request: TriageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    threshold = _get_calibrated_threshold(request.model_name, db)

    start_time = time.time()
    prediction, confidence = classify_text(evidence.content, model_name=request.model_name)
    explanation = generate_explanation(evidence.content, model_name=request.model_name)
    explanation_summary = ", ".join([f"{f['term']}: {f['impact']}" for f in explanation.get("top_features", [])[:5]])
    risk_level, requires_review = _compute_risk(prediction, confidence, threshold=threshold)
    processing_time_ms = int((time.time() - start_time) * 1000)

    result = ClassificationResult(
        evidence_id=evidence.id,
        model_name=request.model_name,
        model_version="1.0",
        prediction=prediction,
        confidence_score=confidence,
        risk_level=risk_level,
        threshold=threshold,
        processing_time_ms=processing_time_ms,
        preprocessing_steps=PREPROCESSING_STEPS,
        explanation_method=explanation.get("method"),
        explanation_summary=explanation_summary,
    )
    db.add(result)
    db.commit()

    save_explanations(db, evidence.id, request.model_name, "1.0", explanation)

    evidence.status = EvidenceStatus.TRIAGED
    create_audit_log(db, evidence.id, "EVIDENCE_TRIAGED", current_user.email, {
        "model": request.model_name,
        "prediction": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "requires_further_review": requires_review,
        "threshold": threshold,
        "processing_time_ms": processing_time_ms,
        "mode": "quick",
    })
    tracker = ChainOfCustodyTracker(db)
    tracker.record_action(evidence.id, "CLASSIFICATION", current_user.id)
    db.commit()

    return TriageResponse(
        evidence_id=evidence.id,
        prediction=prediction,
        confidence=confidence,
        risk_level=risk_level,
        requires_further_review=requires_review,
        model_version="1.0",
        threshold=threshold,
        processing_time_ms=processing_time_ms,
        preprocessing_steps=PREPROCESSING_STEPS,
        explanation_method=explanation.get("method"),
        explanation_summary=explanation_summary,
        top_features=explanation.get("top_features", []),
        model_agreement=None,
    )


@router.post("/ensemble/{evidence_id}", response_model=EnsembleResponse)
def ensemble_triage(evidence_id: int, request: EnsembleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    votes = []
    explanations = []
    start_time = time.time()

    for model_name in request.model_names:
        try:
            result = classify_text_with_explanation(evidence.content, model_name=model_name)
            votes.append({
                "model_name": model_name,
                "prediction": result["prediction"],
                "confidence": result["confidence"],
            })
            if result.get("explanation", {}).get("top_features"):
                explanations.append({
                    "model_name": model_name,
                    "top_features": result["explanation"]["top_features"],
                    "method": result["explanation"].get("method", "unavailable"),
                })
        except Exception:
            votes.append({
                "model_name": model_name,
                "prediction": "error",
                "confidence": 0.0,
            })

    processing_time_ms = int((time.time() - start_time) * 1000)

    cyberbullying_votes = [v for v in votes if v["prediction"] != "not_cyberbullying" and v["prediction"] != "error"]
    if cyberbullying_votes:
        best_vote = max(cyberbullying_votes, key=lambda v: v["confidence"])
        prediction = best_vote["prediction"]
        confidence = best_vote["confidence"]
    else:
        successful_votes = [v for v in votes if v["prediction"] != "error"]
        prediction = "not_cyberbullying"
        confidence = max([v["confidence"] for v in successful_votes], default=0.0)

    primary_model = request.model_names[0] if request.model_names else "svm"
    threshold = _get_calibrated_threshold(primary_model, db)

    agreement = _check_model_agreement(votes)

    risk_level, requires_review = _compute_risk(prediction, confidence, threshold=threshold)
    if agreement.get("forced_review"):
        requires_review = True

    top_features = []
    explanation_method = "ensemble"
    if explanations:
        first_exp = explanations[0]
        explanation_method = f"ensemble ({first_exp['method']})"
        top_features = first_exp["top_features"][:10]

    explanation_summary = ", ".join([f"{f['term']}: {f['impact']}" for f in top_features[:5]])

    result = ClassificationResult(
        evidence_id=evidence.id,
        model_name="ensemble",
        model_version="1.0",
        prediction=prediction,
        confidence_score=confidence,
        risk_level=risk_level,
        threshold=threshold,
        processing_time_ms=processing_time_ms,
        preprocessing_steps=PREPROCESSING_STEPS,
        explanation_method=explanation_method,
        explanation_summary=explanation_summary,
    )
    db.add(result)
    db.commit()

    save_explanations(db, evidence.id, "ensemble", "1.0", {"top_features": top_features, "method": explanation_method})

    evidence.status = EvidenceStatus.TRIAGED
    create_audit_log(db, evidence.id, "EVIDENCE_TRIAGED", current_user.email, {
        "model": "ensemble",
        "models": request.model_names,
        "votes": votes,
        "prediction": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "requires_further_review": requires_review,
        "threshold": threshold,
        "processing_time_ms": processing_time_ms,
        "model_agreement": agreement,
        "mode": "ensemble",
    })
    tracker = ChainOfCustodyTracker(db)
    tracker.record_action(evidence.id, "CLASSIFICATION", current_user.id)
    db.commit()

    return EnsembleResponse(
        evidence_id=evidence.id,
        prediction=prediction,
        confidence=confidence,
        risk_level=risk_level,
        requires_further_review=requires_review,
        threshold=threshold,
        processing_time_ms=processing_time_ms,
        preprocessing_steps=PREPROCESSING_STEPS,
        explanation_method=explanation_method,
        explanation_summary=explanation_summary,
        top_features=top_features,
        votes=[ModelVote(**v) for v in votes],
        model_agreement=agreement,
    )
