import json

from app.models import AuditLog
from app.services.audit_service import create_audit_log, verify_audit_chain
from app.services.chain_of_custody import ChainOfCustodyTracker


def test_audit_log_preserves_actor_event_and_structured_details(db_session, evidence, examiner):
    create_audit_log(
        db_session,
        evidence.id,
        "EVIDENCE_TRIAGED",
        examiner.email,
        {"model": "svm", "threshold": 0.7},
    )
    audit = db_session.query(AuditLog).one()
    assert audit.actor == examiner.email
    assert audit.event_type == "EVIDENCE_TRIAGED"
    assert json.loads(audit.event_details)["threshold"] == 0.7
    assert audit.created_at is not None


def test_chain_of_custody_records_ordered_actions(db_session, evidence, examiner):
    tracker = ChainOfCustodyTracker(db_session)
    tracker.record_action(evidence.id, "UPLOAD", examiner.id)
    tracker.record_action(evidence.id, "CLASSIFICATION", examiner.id)

    history = tracker.get_history(evidence.id)
    assert [entry.action for entry in history] == ["UPLOAD", "CLASSIFICATION"]
    assert all(entry.performed_by == examiner.id for entry in history)


def test_hash_linked_audit_and_custody_chains_verify(db_session, evidence, examiner):
    create_audit_log(db_session, evidence.id, "EVIDENCE_UPLOADED", examiner.email)
    create_audit_log(db_session, evidence.id, "EVIDENCE_TRIAGED", examiner.email)
    tracker = ChainOfCustodyTracker(db_session)
    tracker.record_action(evidence.id, "UPLOAD", examiner.id)
    tracker.record_action(evidence.id, "CLASSIFICATION", examiner.id)

    assert verify_audit_chain(db_session, evidence.id)["valid"] is True
    assert tracker.verify_chain(evidence.id)["valid"] is True
