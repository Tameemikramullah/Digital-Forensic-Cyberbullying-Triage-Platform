from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security.auth import get_current_user
from ..services.export_service import build_evidence_report
from ..services.pdf_export_service import generate_forensic_pdf

router = APIRouter()


@router.get("/evidence/{evidence_id}/export")
def export_evidence(evidence_id: int, format: str = "json", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = build_evidence_report(db, evidence_id, format=format)
    if format == "pdf":
        pdf_bytes = generate_forensic_pdf(report)
        from fastapi.responses import Response
        return Response(content=pdf_bytes, media_type="application/pdf")
    return report
