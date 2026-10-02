from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import ExaminerReviewCreate, ExaminerReviewRead
from ..models import User, Evidence, EvidenceStatus, ExaminerReview
from ..security.auth import get_current_user
from ..services.audit_service import create_audit_log
from ..services.chain_of_custody import ChainOfCustodyTracker

router = APIRouter()


@router.post("", response_model=ExaminerReviewRead)
def create_review(review_in: ExaminerReviewCreate, evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    review = ExaminerReview(
        evidence_id=evidence_id,
        examiner_id=current_user.id,
        decision=review_in.decision,
        notes=review_in.notes,
    )
    db.add(review)
    evidence.status = EvidenceStatus.REVIEWED
    create_audit_log(db, evidence.id, "EVIDENCE_REVIEWED", current_user.email, {"decision": review_in.decision})
    tracker = ChainOfCustodyTracker(db)
    tracker.record_action(evidence.id, "REVIEW", current_user.id)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{evidence_id}", response_model=list[ExaminerReviewRead])
def get_reviews(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ExaminerReview).filter(ExaminerReview.evidence_id == evidence_id).all()
