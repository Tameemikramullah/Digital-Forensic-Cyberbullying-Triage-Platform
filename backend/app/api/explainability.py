from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.explanation_service import get_explanations

router = APIRouter()


@router.get("/evidence/{evidence_id}/explanations")
def get_evidence_explanations(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    explanations = get_explanations(db, evidence_id)
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
