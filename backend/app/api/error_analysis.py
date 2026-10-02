from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.error_analysis import compute_error_analysis

router = APIRouter()


@router.get("/error-analysis")
def get_error_analysis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return compute_error_analysis(db)
