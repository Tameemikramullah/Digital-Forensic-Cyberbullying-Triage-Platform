import pytest
from app.services.evidence_service import create_evidence, get_evidence, list_evidence, delete_evidence
from app.schemas import EvidenceCreate, EvidenceMetadataCreate


def test_create_evidence(db_session, test_user):
    evidence_in = EvidenceCreate(
        source_platform="Twitter",
        source_post_id="tweet_456",
        content="Sample evidence content",
        acquisition_date="2026-01-01T00:00:00Z",
        metadata=EvidenceMetadataCreate(
            author_name="Test Author",
            source_url="https://example.com",
            filename="test.txt",
            filesize=1234,
        ),
    )
    evidence = create_evidence(db_session, evidence_in, test_user.id)
    assert evidence.id is not None
    assert evidence.source_platform == "Twitter"
    assert evidence.evidence_hash is not None
    assert evidence.status == "PENDING"


def test_get_evidence(db_session, test_evidence):
    found = get_evidence(db_session, test_evidence.id)
    assert found is not None
    assert found.id == test_evidence.id
    assert found.content == test_evidence.content


def test_list_evidence(db_session, test_evidence):
    evidence_list = list_evidence(db_session)
    assert len(evidence_list) >= 1
    assert any(e.id == test_evidence.id for e in evidence_list)


def test_delete_evidence(db_session, test_evidence):
    delete_evidence(db_session, test_evidence)
    found = get_evidence(db_session, test_evidence.id)
    assert found is None
