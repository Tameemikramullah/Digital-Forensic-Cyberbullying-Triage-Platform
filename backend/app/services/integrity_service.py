import hashlib
import os
from sqlalchemy.orm import Session
from ..models import Evidence, IntegrityCheck
from datetime import datetime


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_integrity(db: Session, evidence_id: int) -> dict:
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise ValueError("Evidence not found")

    original_hash = evidence.evidence_hash
    # A file-backed item must be verified against the acquired original bytes,
    # not against the separately stored/extracted text used for ML inference.
    if evidence.original_file_path:
        if not os.path.isfile(evidence.original_file_path):
            raise FileNotFoundError("Original evidence file is unavailable for verification")
        with open(evidence.original_file_path, "rb") as evidence_file:
            current_hash = compute_sha256(evidence_file.read())
    else:
        current_hash = compute_sha256(evidence.content.encode("utf-8"))
    match = original_hash == current_hash

    integrity_check = IntegrityCheck(
        evidence_id=evidence_id,
        original_hash=original_hash,
        current_hash=current_hash,
        match=1 if match else 0,
    )
    db.add(integrity_check)
    db.commit()
    db.refresh(integrity_check)

    return {
        "evidence_id": evidence_id,
        "original_hash": original_hash,
        "current_hash": current_hash,
        "match": match,
        "status": "VERIFIED" if match else "HASH_MISMATCH",
        "checked_at": integrity_check.checked_at.isoformat() if integrity_check.checked_at else datetime.now().isoformat(),
    }


def get_integrity_checks(db: Session, evidence_id: int):
    return db.query(IntegrityCheck).filter(IntegrityCheck.evidence_id == evidence_id).order_by(IntegrityCheck.checked_at.desc()).all()
