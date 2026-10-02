import json
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.app.models import Evidence, ClassificationResult, ExaminerReview, AuditLog


def build_evidence_report(db: Session, evidence_id: int, format: str = "json") -> Any:
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise ValueError("Evidence not found")

    classification = db.query(ClassificationResult).filter(ClassificationResult.evidence_id == evidence_id).first()
    reviews = db.query(ExaminerReview).filter(ExaminerReview.evidence_id == evidence_id).all()
    audit_logs = db.query(AuditLog).filter(AuditLog.evidence_id == evidence_id).order_by(AuditLog.created_at.asc()).all()

    report = {
        "evidence_id": evidence.id,
        "evidence_hash": evidence.evidence_hash,
        "source_platform": evidence.source_platform,
        "source_post_id": evidence.source_post_id,
        "content": evidence.content,
        "acquisition_date": evidence.acquisition_date.isoformat() if evidence.acquisition_date else None,
        "uploaded_by": evidence.uploaded_by,
        "status": evidence.status.value,
        "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
        "metadata": {
            "author_name": evidence.evidence_metadata.author_name if evidence.evidence_metadata else None,
            "source_url": evidence.evidence_metadata.source_url if evidence.evidence_metadata else None,
            "original_timestamp": evidence.evidence_metadata.original_timestamp.isoformat() if evidence.evidence_metadata and evidence.evidence_metadata.original_timestamp else None,
            "filename": evidence.evidence_metadata.filename if evidence.evidence_metadata else None,
            "filesize": evidence.evidence_metadata.filesize if evidence.evidence_metadata else None,
        },
        "triage": {
            "model_name": classification.model_name if classification else None,
            "model_version": classification.model_version if classification else None,
            "prediction": classification.prediction if classification else None,
            "confidence_score": classification.confidence_score if classification else None,
            "risk_level": classification.risk_level if classification else None,
            "threshold": classification.threshold if classification else None,
            "processing_time_ms": classification.processing_time_ms if classification else None,
            "preprocessing_steps": classification.preprocessing_steps if classification else None,
            "explanation_method": classification.explanation_method if classification else None,
            "explanation_summary": classification.explanation_summary if classification else None,
            "created_at": classification.created_at.isoformat() if classification else None,
        },
        "examiner_reviews": [
            {
                "id": r.id,
                "examiner_id": r.examiner_id,
                "decision": r.decision,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ],
        "audit_trail": [
            {
                "id": log.id,
                "actor": log.actor,
                "event_type": log.event_type,
                "event_details": json.loads(log.event_details) if log.event_details else None,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in audit_logs
        ],
        "exported_at": None,
    }

    return report
