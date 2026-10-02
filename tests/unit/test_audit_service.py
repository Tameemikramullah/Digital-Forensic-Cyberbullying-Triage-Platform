import pytest
from app.services.audit_service import create_audit_log
from app.models import AuditLog


def test_create_audit_log(db_session, test_evidence):
    audit = create_audit_log(
        db_session,
        evidence_id=test_evidence.id,
        event_type="EVIDENCE_UPLOADED",
        actor="test_user",
        event_details={"source_platform": "Twitter"},
    )
    assert audit.id is not None
    assert audit.evidence_id == test_evidence.id
    assert audit.event_type == "EVIDENCE_UPLOADED"
    assert audit.actor == "test_user"
    assert audit.event_details is not None


def test_audit_log_ordering(db_session, test_evidence):
    create_audit_log(db_session, test_evidence.id, "FIRST", "user1")
    create_audit_log(db_session, test_evidence.id, "SECOND", "user2")
    logs = db_session.query(AuditLog).filter(AuditLog.evidence_id == test_evidence.id).order_by(AuditLog.created_at.asc()).all()
    assert len(logs) == 2
    assert logs[0].event_type == "FIRST"
    assert logs[1].event_type == "SECOND"
