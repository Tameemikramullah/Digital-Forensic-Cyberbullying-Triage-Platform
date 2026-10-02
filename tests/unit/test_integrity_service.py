import pytest
from datetime import datetime
from app.services.integrity_service import verify_integrity, get_integrity_checks
from app.services.hash_service import generate_hash


def test_verify_integrity_match(db_session, test_user):
    from app.models import Evidence, EvidenceStatus
    content = "Test content for integrity"
    evidence_hash = generate_hash(content)
    evidence = Evidence(
        evidence_hash=evidence_hash,
        source_platform="Twitter",
        source_post_id="tweet_456",
        content=content,
        acquisition_date=datetime(2026, 1, 1, 0, 0, 0),
        uploaded_by=test_user.id,
        status=EvidenceStatus.PENDING,
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    result = verify_integrity(db_session, evidence.id)
    assert result["evidence_id"] == evidence.id
    assert result["match"] is True
    assert result["status"] == "VERIFIED"
    assert "checked_at" in result


def test_verify_integrity_creates_record(db_session, test_user):
    from app.models import Evidence, EvidenceStatus
    content = "Test content for integrity record"
    evidence_hash = generate_hash(content)
    evidence = Evidence(
        evidence_hash=evidence_hash,
        source_platform="Twitter",
        source_post_id="tweet_789",
        content=content,
        acquisition_date=datetime(2026, 1, 1, 0, 0, 0),
        uploaded_by=test_user.id,
        status=EvidenceStatus.PENDING,
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    checks_before = get_integrity_checks(db_session, evidence.id)
    assert len(checks_before) == 0

    verify_integrity(db_session, evidence.id)
    checks_after = get_integrity_checks(db_session, evidence.id)
    assert len(checks_after) == 1
    assert checks_after[0].match == 1


def test_verify_integrity_missing_evidence(db_session):
    with pytest.raises(ValueError):
        verify_integrity(db_session, 99999)
