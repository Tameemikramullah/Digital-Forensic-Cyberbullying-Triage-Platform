from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.model_comparison import run_inter_model_comparison
from ml.model_registry import run_training_pipeline, get_model_registry, retrain_model

router = APIRouter()


@router.get("/model-comparison")
def get_model_comparison(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return run_inter_model_comparison(db)


@router.post("/train")
def train_models(
    model_names: str = "svm,logistic,naive_bayes,cnn,bert",
    dataset_path: str = None,
    current_user: User = Depends(get_current_user),
):
    try:
        names = [m.strip() for m in model_names.split(",") if m.strip()]
        result = run_training_pipeline(model_names=names, dataset_path=dataset_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/registry")
def get_registry(current_user: User = Depends(get_current_user)):
    return get_model_registry()


@router.post("/retrain/{model_name}")
def retrain_single_model(model_name: str, current_user: User = Depends(get_current_user)):
    try:
        result = retrain_model(model_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")
