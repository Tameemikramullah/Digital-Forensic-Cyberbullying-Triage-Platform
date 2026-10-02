from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ExaminerReviewCreate(BaseModel):
    decision: str
    notes: Optional[str] = None


class ExaminerReviewRead(BaseModel):
    id: int
    evidence_id: int
    examiner_id: int
    decision: str
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogRead(BaseModel):
    id: int
    evidence_id: int
    actor: str
    event_type: str
    event_details: Optional[str]
    created_at: datetime
    previous_hash: Optional[str]
    entry_hash: Optional[str]

    model_config = {"from_attributes": True}


class ChainOfCustodyRead(BaseModel):
    id: int
    evidence_id: int
    action: str
    performed_by: int
    timestamp: datetime
    previous_hash: Optional[str]
    entry_hash: Optional[str]

    model_config = {"from_attributes": True}
