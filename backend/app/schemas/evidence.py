from pydantic import BaseModel, Field, FilePath
from datetime import datetime
from typing import Optional, List, Any
from ..models import EvidenceStatus


class EvidenceMetadataBase(BaseModel):
    author_name: Optional[str] = None
    source_url: Optional[str] = None
    original_timestamp: Optional[datetime] = None
    filename: Optional[str] = None
    filesize: Optional[int] = None


class EvidenceMetadataCreate(EvidenceMetadataBase):
    pass


class EvidenceMetadataRead(EvidenceMetadataBase):
    id: int
    evidence_id: int

    model_config = {"from_attributes": True}


class EvidenceBase(BaseModel):
    source_platform: str
    source_post_id: str
    content: str
    acquisition_date: datetime


class EvidenceCreate(EvidenceBase):
    metadata: Optional[EvidenceMetadataCreate] = None
    original_file_path: Optional[str] = None
    original_filesize: Optional[int] = None


class EvidenceRead(EvidenceBase):
    id: int
    evidence_hash: str
    uploaded_by: int
    status: EvidenceStatus
    created_at: datetime
    evidence_metadata: Optional[EvidenceMetadataRead] = None
    original_file_path: Optional[str] = None
    original_filesize: Optional[int] = None

    model_config = {"from_attributes": True}


class EvidenceList(BaseModel):
    id: int
    evidence_hash: str
    source_platform: str
    source_post_id: str
    status: EvidenceStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceBulkCreate(BaseModel):
    items: List[EvidenceCreate]


class EvidenceBulkResult(BaseModel):
    created: List[Any] = []
    skipped: List[dict] = []
    errors: List[str] = []
