from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.model_evaluation import compute_model_evaluation

router = APIRouter()


@router.get("/evaluation")
def get_model_evaluation(
    model_name: str = Query(None, description="Filter by model name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return compute_model_evaluation(db, model_name=model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
