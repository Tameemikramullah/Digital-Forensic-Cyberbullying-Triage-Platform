from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time
from typing import List, Dict, Any
from ..database import get_db
from ..schemas import TriageRequest, TriageResponse, EnsembleRequest, EnsembleResponse, ModelVote
from ..models import User, Evidence, EvidenceStatus, ClassificationResult
from ..security.auth import get_current_user
from ..services.classification_service import (
    CANONICAL_LABELS,
    classify_text_with_explanation,
    classify_text_with_scores,
)
from ..services.explanation_service import generate_explanation, save_explanations
from ..services.audit_service import create_audit_log
from ..services.chain_of_custody import ChainOfCustodyTracker

router = APIRouter()


def _get_calibrated_threshold(model_name: str, db: Session) -> float:
    try:
        from ..services.threshold_calibration import run_threshold_calibration
        calibration = run_threshold_calibration(model_name=model_name, db=db)
        if calibration.get("results"):
            return float(calibration.get("selected_threshold", 0.7))
    except Exception:
        pass
    return 0.7


def _compute_risk(risk_score: float | None, threshold: float = 0.7) -> tuple[str, bool]:
    """LOW below threshold; MEDIUM from threshold to high cutoff; HIGH at high cutoff."""
    if risk_score is None:
        return "UNKNOWN", True
    if risk_score < threshold:
        return "LOW", False
    if risk_score >= max(threshold, 0.8):
        return "HIGH", True
    return "MEDIUM", True


def _plurality_vote(votes: List[dict]) -> Dict[str, Any]:
    """Use one equal-weight vote per model; ignore model-specific confidence values."""
    successful = [vote for vote in votes if vote.get("prediction") in CANONICAL_LABELS]
    if not successful:
        return {
            "prediction": "unavailable", "confidence": 0.0, "risk_score": 0.0,
            "vote_counts": {}, "tie": False, "valid_votes": 0,
        }
    counts = {}
    for vote in successful:
        label = str(vote["prediction"])
        counts[label] = counts.get(label, 0) + 1
    highest_count = max(counts.values())
    tied_labels = sorted(label for label, count in counts.items() if count == highest_count)
    prediction = tied_labels[0]
    total = len(successful)
    cyberbullying_votes = sum(vote["prediction"] != "not_cyberbullying" for vote in successful)
    return {
        "prediction": prediction,
        "confidence": highest_count / total,
        "risk_score": cyberbullying_votes / total,
        "vote_counts": counts,
        "tie": len(tied_labels) > 1,
        "valid_votes": total,
    }


def _check_model_agreement(votes: List[dict]) -> Dict[str, Any]:
    successful_votes = [v for v in votes if v.get("prediction") in CANONICAL_LABELS]
    if not successful_votes:
        return {"agreement": "unknown", "confidence_spread": None, "disagreement_levels": 0, "unique_predictions": [], "forced_review": True}
    predictions = [v["prediction"] for v in successful_votes]
    unique_predictions = sorted(set(predictions))
    counts = {label: predictions.count(label) for label in unique_predictions}
    plurality_count = max(counts.values())
    tie = sum(count == plurality_count for count in counts.values()) > 1
    agreement = "full" if len(unique_predictions) == 1 else "partial" if len(unique_predictions) == 2 else "none"
    forced_review = tie or len(unique_predictions) > 2
    return {
        "agreement": agreement,
        "confidence_spread": None,
        "disagreement_levels": len(unique_predictions),
        "unique_predictions": unique_predictions,
        "vote_counts": counts,
        "winning_vote_share": plurality_count / len(successful_votes),
        "tie": tie,
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
    scores = classify_text_with_scores(evidence.content, model_name=request.model_name)
    prediction, confidence = scores["prediction"], scores["confidence"]
    risk_score = scores["risk_score"]
    explanation = generate_explanation(evidence.content, model_name=request.model_name)
    explanation_summary = ", ".join([f"{f['term']}: {f['impact']}" for f in explanation.get("top_features", [])[:5]])
    risk_level, requires_review = _compute_risk(risk_score, threshold=threshold)
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
        "risk_score": risk_score,
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
        risk_score=risk_score,
        risk_level=risk_level,
        requires_further_review=requires_review,
        model_version="1.0",
        threshold=threshold,
        processing_time_ms=processing_time_ms,
        preprocessing_steps=PREPROCESSING_STEPS,
        explanation_method=explanation.get("method"),
        explanation_reason=explanation.get("reason"),
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

    model_names = list(dict.fromkeys(request.model_names))
    for model_name in model_names:
        try:
            result = classify_text_with_explanation(evidence.content, model_name=model_name)
            explanation = result.get("explanation", {})
            explanation_available = bool(explanation.get("top_features"))
            votes.append({
                "model_name": model_name,
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "explanation_available": explanation_available,
                "explanation_method": explanation.get("method", "unavailable"),
                "explanation_reason": explanation.get("reason"),
            })
            if explanation_available:
                explanations.append({
                    "model_name": model_name,
                    "top_features": explanation["top_features"],
                    "method": explanation.get("method", "unavailable"),
                })
        except Exception:
            votes.append({
                "model_name": model_name,
                "prediction": "error",
                "confidence": 0.0,
                "explanation_available": False,
                "explanation_method": "unavailable",
                "explanation_reason": "Model inference failed.",
            })

    processing_time_ms = int((time.time() - start_time) * 1000)

    aggregate = _plurality_vote(votes)
    prediction = aggregate["prediction"]
    confidence = aggregate["confidence"]
    risk_score = aggregate["risk_score"]
    best_vote = next((v for v in votes if v["prediction"] == prediction), None)

    threshold = 0.5  # minimum cyberbullying vote share for ensemble MEDIUM risk

    agreement = _check_model_agreement(votes)

    if aggregate["valid_votes"] == 0:
        risk_level, requires_review = "UNKNOWN", True
    else:
        risk_level, requires_review = _compute_risk(risk_score, threshold=threshold)
    if agreement.get("forced_review") or aggregate["valid_votes"] == 0:
        requires_review = True

    top_features = []
    selected_model = best_vote["model_name"] if best_vote else None
    selected_explanation = next((item for item in explanations if item["model_name"] == selected_model), None)
    if selected_explanation:
        explanation_method = selected_explanation["method"]
        top_features = selected_explanation["top_features"][:10]
    else:
        explanation_method = f"unavailable ({selected_model or 'no selected model'})"

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
        "models": model_names,
        "votes": votes,
        "prediction": prediction,
        "confidence": confidence,
        "risk_score": risk_score,
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
        risk_score=risk_score,
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
