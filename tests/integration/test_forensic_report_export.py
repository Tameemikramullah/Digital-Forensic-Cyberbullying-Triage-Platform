from app.models import ClassificationResult, ExaminerReview
from app.services.audit_service import create_audit_log
from app.services.export_service import build_evidence_report


def test_export_contains_triage_review_and_audit_trail(db_session, evidence, examiner):
    db_session.add(ClassificationResult(
        evidence_id=evidence.id,
        model_name="svm",
        model_version="1.0",
        prediction="gender",
        confidence_score=0.81,
        threshold=0.7,
        risk_level="HIGH",
    ))
    db_session.add(ExaminerReview(
        evidence_id=evidence.id,
        examiner_id=examiner.id,
        decision="CONFIRMED",
        notes="Relevant for examiner review.",
    ))
    db_session.commit()
    create_audit_log(db_session, evidence.id, "EVIDENCE_TRIAGED", examiner.email)

    report = build_evidence_report(db_session, evidence.id)
    assert report["evidence_hash"] == evidence.evidence_hash
    assert report["triage"]["prediction"] == "gender"
    assert report["examiner_reviews"][0]["decision"] == "CONFIRMED"
    assert report["audit_trail"][0]["event_type"] == "EVIDENCE_TRIAGED"
