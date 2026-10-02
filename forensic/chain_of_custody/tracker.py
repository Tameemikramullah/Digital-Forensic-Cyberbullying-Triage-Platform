from sqlalchemy.orm import Session
from backend.app.models import ChainOfCustody, ChainAction
from datetime import datetime


class ChainOfCustodyTracker:
    def __init__(self, db: Session):
        self.db = db

    def record_action(self, evidence_id: int, action: str, performed_by: int):
        record = ChainOfCustody(
            evidence_id=evidence_id,
            action=action,
            performed_by=performed_by,
        )
        self.db.add(record)
        self.db.commit()
        return record

    def get_history(self, evidence_id: int):
        return self.db.query(ChainOfCustody).filter(ChainOfCustody.evidence_id == evidence_id).order_by(ChainOfCustody.timestamp.asc()).all()
