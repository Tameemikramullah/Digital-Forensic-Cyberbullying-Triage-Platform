from sqlalchemy.orm import Session
from backend.app.models import AuditLog
from typing import Optional
import json


def log_action(db: Session, evidence_id: int, action: str, performed_by: int, details: Optional[dict] = None):
    audit = AuditLog(
        evidence_id=evidence_id,
        action=action,
        performed_by=performed_by,
        details_json=json.dumps(details) if details else None,
    )
    db.add(audit)
    db.commit()
    return audit
