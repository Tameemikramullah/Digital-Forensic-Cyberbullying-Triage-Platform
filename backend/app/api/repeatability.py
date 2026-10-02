from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.repeatability_service import run_repeatability_test

router = APIRouter()


@router.post("/evidence/{evidence_id}/repeatability")
def repeatability_test(evidence_id: int, model_name: str = "svm", iterations: int = 10, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = run_repeatability_test(db, evidence_id, model_name=model_name, iterations=iterations)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
