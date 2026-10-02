from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.operational_evaluation import compute_operational_metrics, run_simulated_cases

router = APIRouter()


@router.get("/operational-metrics")
def operational_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return compute_operational_metrics(db)


@router.get("/simulated-cases")
def simulated_cases(model_name: str = "svm", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return run_simulated_cases(db=db, model_name=model_name)
