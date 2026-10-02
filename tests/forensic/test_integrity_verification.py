from app.models import IntegrityCheck
from app.services.evidence_service import create_evidence
from app.services.hash_service import generate_hash_from_bytes
from app.services.integrity_service import verify_integrity
from app.schemas.evidence import EvidenceCreate
from datetime import datetime, timezone


def test_integrity_verification_records_a_matching_hash(db_session, evidence):
    result = verify_integrity(db_session, evidence.id)

    assert result["status"] == "VERIFIED"
    assert result["match"] is True
    check = db_session.query(IntegrityCheck).one()
    assert check.original_hash == check.current_hash


def test_integrity_verification_detects_tampered_content(db_session, evidence):
    evidence.content = "Tampered after acquisition"
    db_session.commit()

    result = verify_integrity(db_session, evidence.id)
    assert result["status"] == "HASH_MISMATCH"
    assert result["match"] is False


def test_integrity_verification_uses_original_file_bytes(db_session, examiner, monkeypatch, tmp_path):
    """File-backed evidence must not be compared with its extracted text."""
    import app.services.evidence_service as evidence_service

    monkeypatch.setattr(evidence_service, "EVIDENCE_FILES_DIR", str(tmp_path))
    raw_file = b"original acquisition bytes\x00\xff"
    item = create_evidence(
        db_session,
        EvidenceCreate(
            source_platform="Twitter",
            source_post_id="file-backed-001",
            content="Extracted text is intentionally different from raw bytes.",
            acquisition_date=datetime.now(timezone.utc),
        ),
        examiner.id,
        file_bytes=raw_file,
        original_filename="evidence.bin",
    )

    assert item.evidence_hash == generate_hash_from_bytes(raw_file)
    assert verify_integrity(db_session, item.id)["status"] == "VERIFIED"
