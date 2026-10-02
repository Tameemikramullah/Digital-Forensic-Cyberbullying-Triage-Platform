from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AuditLog, ChainOfCustody, User
from ..schemas import AuditLogRead, ChainOfCustodyRead
from ..security.auth import get_current_user
from ..services.audit_service import verify_audit_chain
from ..services.chain_of_custody import ChainOfCustodyTracker

router = APIRouter()


@router.get("/{evidence_id}", response_model=list[AuditLogRead])
def get_audit_logs(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(AuditLog).filter(AuditLog.evidence_id == evidence_id).order_by(AuditLog.created_at.desc()).all()


@router.get("/chain-of-custody/{evidence_id}", response_model=list[ChainOfCustodyRead])
def get_chain_of_custody(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ChainOfCustody).filter(ChainOfCustody.evidence_id == evidence_id).order_by(ChainOfCustody.timestamp.desc()).all()


@router.get("/verify/{evidence_id}")
def verify_audit_and_custody(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit_result = verify_audit_chain(db, evidence_id)
    tracker = ChainOfCustodyTracker(db)
    custody_result = tracker.verify_chain(evidence_id)
    return {
        "evidence_id": evidence_id,
        "audit_chain": audit_result,
        "custody_chain": custody_result,
        "overall_valid": audit_result.get("valid") and custody_result.get("valid"),
    }
