from fastapi import APIRouter, Depends
from ..security.auth import get_current_user
from ..services.reproducibility_service import get_reproducibility_report, run_reproducibility_test

router = APIRouter()


@router.get("/reproducibility-report")
def reproducibility_report(current_user = Depends(get_current_user)):
    return get_reproducibility_report()


@router.get("/reproducibility-test")
def reproducibility_test(model_name: str = "svm", current_user = Depends(get_current_user)):
    try:
        return run_reproducibility_test(model_name=model_name)
    except FileNotFoundError as e:
        return {"error": str(e), "model_name": model_name}