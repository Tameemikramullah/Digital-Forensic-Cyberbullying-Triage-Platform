import os
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..models import Evidence, EvidenceMetadata, EvidenceStatus
from ..config import settings
from ..services.hash_service import generate_hash, generate_hash_from_bytes


UPLOAD_ROOT = os.path.abspath(settings.UPLOAD_DIR)
EVIDENCE_FILES_DIR = os.path.join(UPLOAD_ROOT, "evidence_files")


def _ensure_dirs():
    os.makedirs(EVIDENCE_FILES_DIR, exist_ok=True)


def _store_evidence_file(evidence_id: int, filename: str, data: bytes) -> str:
    _ensure_dirs()
    ext = os.path.splitext(filename)[1]
    stored_name = f"{evidence_id}{ext}"
    dest = os.path.join(EVIDENCE_FILES_DIR, stored_name)
    with open(dest, "wb") as f:
        f.write(data)
    return dest


def create_evidence(db: Session, evidence_in, uploaded_by: int, file_bytes: Optional[bytes] = None, original_filename: Optional[str] = None) -> Evidence:
    if file_bytes is not None:
        evidence_hash = generate_hash_from_bytes(file_bytes)
    else:
        evidence_hash = generate_hash(evidence_in.content)

    existing = db.query(Evidence).filter(Evidence.evidence_hash == evidence_hash).first()
    if existing:
        raise ValueError("Evidence with this content hash already exists")

    evidence = Evidence(
        evidence_hash=evidence_hash,
        source_platform=evidence_in.source_platform,
        source_post_id=evidence_in.source_post_id,
        content=evidence_in.content,
        acquisition_date=evidence_in.acquisition_date,
        uploaded_by=uploaded_by,
        status=EvidenceStatus.PENDING,
    )
    db.add(evidence)
    db.flush()

    original_file_path = None
    original_filesize = None
    if file_bytes is not None and original_filename:
        original_file_path = _store_evidence_file(evidence.id, original_filename, file_bytes)
        original_filesize = len(file_bytes)
        evidence.original_file_path = original_file_path
        evidence.original_filesize = original_filesize

    if evidence_in.metadata:
        metadata = EvidenceMetadata(
            evidence_id=evidence.id,
            author_name=evidence_in.metadata.author_name,
            source_url=evidence_in.metadata.source_url,
            original_timestamp=evidence_in.metadata.original_timestamp,
            filename=original_filename or evidence_in.metadata.filename,
            filesize=original_filesize or evidence_in.metadata.filesize,
        )
        db.add(metadata)

    db.commit()
    db.refresh(evidence)
    return evidence


def bulk_create_evidence(db: Session, items: List[Any], uploaded_by: int) -> Dict[str, Any]:
    created = []
    skipped = []
    errors = []

    for idx, evidence_in in enumerate(items):
        try:
            evidence_hash = generate_hash(evidence_in.content)
            existing = db.query(Evidence).filter(Evidence.evidence_hash == evidence_hash).first()
            if existing:
                skipped.append({
                    "index": idx,
                    "source_post_id": evidence_in.source_post_id,
                    "reason": "Duplicate hash",
                })
                continue

            evidence = Evidence(
                evidence_hash=evidence_hash,
                source_platform=evidence_in.source_platform,
                source_post_id=evidence_in.source_post_id,
                content=evidence_in.content,
                acquisition_date=evidence_in.acquisition_date,
                uploaded_by=uploaded_by,
                status=EvidenceStatus.PENDING,
            )
            db.add(evidence)
            db.flush()

            if evidence_in.metadata:
                metadata = EvidenceMetadata(
                    evidence_id=evidence.id,
                    author_name=evidence_in.metadata.author_name,
                    source_url=evidence_in.metadata.source_url,
                    original_timestamp=evidence_in.metadata.original_timestamp,
                    filename=evidence_in.metadata.filename,
                    filesize=evidence_in.metadata.filesize,
                )
                db.add(metadata)

            created.append(evidence)
        except Exception as e:
            errors.append(f"Item {idx}: {str(e)}")

    db.commit()
    return {
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }


def get_evidence(db: Session, evidence_id: int) -> Optional[Evidence]:
    return db.query(Evidence).filter(Evidence.id == evidence_id).first()


def list_evidence(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Evidence).order_by(Evidence.created_at.desc()).offset(skip).limit(limit).all()


def delete_evidence(db: Session, evidence: Evidence):
    db.delete(evidence)
    db.commit()
