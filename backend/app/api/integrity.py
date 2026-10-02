from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.explanation_service import get_explanations as get_explanations_service
from ..services.integrity_service import verify_integrity, get_integrity_checks

router = APIRouter()


@router.get("/evidence/{evidence_id}/explanations")
def get_evidence_explanations(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    explanations = get_explanations_service(db, evidence_id)
    return [
        {
            "id": e.id,
            "model_name": e.model_name,
            "model_version": e.model_version,
            "explanation_method": e.explanation_method,
            "feature_name": e.feature_name,
            "contribution": e.contribution,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in explanations
    ]


@router.post("/evidence/{evidence_id}/verify-integrity")
def verify_evidence_integrity(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = verify_integrity(db, evidence_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/evidence/{evidence_id}/integrity-checks")
def get_integrity_check_history(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    checks = get_integrity_checks(db, evidence_id)
    return [
        {
            "id": c.id,
            "original_hash": c.original_hash,
            "current_hash": c.current_hash,
            "match": bool(c.match),
            "checked_at": c.checked_at.isoformat() if c.checked_at else None,
        }
        for c in checks
    ]
