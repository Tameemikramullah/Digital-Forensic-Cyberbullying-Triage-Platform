from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import EvidenceCreate, EvidenceRead, EvidenceList, EvidenceBulkCreate, EvidenceBulkResult
from ..models import User, Evidence
from ..security.auth import get_current_user
from ..services.audit_service import create_audit_log
from ..services.evidence_service import create_evidence, get_evidence, list_evidence, delete_evidence, bulk_create_evidence
from ..services.chain_of_custody import ChainOfCustodyTracker
from typing import List, Optional

router = APIRouter()


@router.post("/upload", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    source_platform: str = Form(...),
    source_post_id: str = Form(...),
    content: str = Form(...),
    acquisition_date: str = Form(...),
    author_name: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    original_timestamp: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    filesize: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    metadata = None
    if author_name or source_url or original_timestamp or filename or filesize:
        from ..schemas import EvidenceMetadataCreate
        metadata = EvidenceMetadataCreate(
            author_name=author_name,
            source_url=source_url,
            original_timestamp=datetime.fromisoformat(original_timestamp) if original_timestamp else None,
            filename=filename,
            filesize=filesize,
        )

    evidence_in = EvidenceCreate(
        source_platform=source_platform,
        source_post_id=source_post_id,
        content=content,
        acquisition_date=datetime.fromisoformat(acquisition_date),
        metadata=metadata,
    )

    file_bytes = None
    original_filename = None
    if file is not None:
        file_bytes = file.file.read()
        original_filename = file.filename

    evidence = create_evidence(db, evidence_in, current_user.id, file_bytes=file_bytes, original_filename=original_filename)
    create_audit_log(db, evidence.id, "EVIDENCE_UPLOADED", current_user.email, {"source_platform": evidence.source_platform})
    tracker = ChainOfCustodyTracker(db)
    tracker.record_action(evidence.id, "UPLOAD", current_user.id)
    return evidence


@router.post("/bulk-upload", response_model=EvidenceBulkResult, status_code=status.HTTP_201_CREATED)
def bulk_upload_evidence(payload: EvidenceBulkCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = bulk_create_evidence(db, payload.items, current_user.id)
    created_ids = [e.id for e in result["created"]]
    if created_ids:
        create_audit_log(db, created_ids[0], "BULK_EVIDENCE_UPLOADED", current_user.email, {
            "created_count": len(result["created"]),
            "skipped_count": len(result["skipped"]),
            "error_count": len(result["errors"]),
            "evidence_ids": created_ids,
        })
    return EvidenceBulkResult(
        created=result["created"],
        skipped=result["skipped"],
        errors=result["errors"],
    )


@router.get("", response_model=List[EvidenceList])
def get_evidence_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_evidence(db)


@router.get("/{evidence_id}", response_model=EvidenceRead)
def get_evidence_by_id(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    evidence = get_evidence(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence_by_id(evidence_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    evidence = get_evidence(db, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    delete_evidence(db, evidence)
    return None
