from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.threshold_calibration import run_threshold_calibration

router = APIRouter()


@router.get("/calibration")
def threshold_calibration(model_name: str = "svm", current_user: User = Depends(get_current_user)):
    try:
        return run_threshold_calibration(model_name=model_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")
