from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
import sys
import os

# Pre-import torch in the main thread before uvicorn's event loop starts.
# triton's native initialiser segfaults when first imported from a non-main
# thread (uvicorn's asyncio loop), so force the import here up front.
try:
    import torch  # noqa: F401
    torch.set_num_threads(4)
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    # transformers pulls in triton lazily; import it up-front in the main
    # thread so triton's native code initialises here, not in the event loop.
    import transformers  # noqa: F401
    from transformers.models.auto import modeling_auto  # noqa: F401
except Exception:
    pass

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

app = FastAPI(title="Digital Forensic Cyberbullying Triage Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api import auth, evidence, triage, reviews, audit, export, integrity, explainability, repeatability, reproducibility, operational, threshold_calibration, model_evaluation, error_analysis, model_comparison  # noqa: E402, F401
from .models import User, Evidence, EvidenceMetadata, ClassificationResult, ExaminerReview, AuditLog, ChainOfCustody, Explanation, RepeatabilityTest, IntegrityCheck  # noqa: E402, F401

try:
    Base.metadata.create_all(bind=engine)
    print("INFO: Database tables created successfully")
except Exception as e:
    print(f"ERROR: Failed to create tables: {e}")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
app.include_router(triage.router, prefix="/triage", tags=["triage"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(integrity.router, prefix="/integrity", tags=["integrity"])
app.include_router(explainability.router, prefix="/explainability", tags=["explainability"])
app.include_router(repeatability.router, prefix="/repeatability", tags=["repeatability"])
app.include_router(reproducibility.router, prefix="/reproducibility", tags=["reproducibility"])
app.include_router(operational.router, prefix="/operational", tags=["operational"])
app.include_router(threshold_calibration.router, prefix="/threshold-calibration", tags=["threshold-calibration"])
app.include_router(model_evaluation.router, prefix="/model-evaluation", tags=["model-evaluation"])
app.include_router(error_analysis.router, prefix="/error-analysis", tags=["error-analysis"])
app.include_router(model_comparison.router, prefix="/model-comparison", tags=["model-comparison"])


@app.get("/health")
def health():
    return {"status": "ok"}
