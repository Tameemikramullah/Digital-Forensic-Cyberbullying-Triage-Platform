import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import ChainOfCustody


def _compute_entry_hash(previous_hash: str | None, action: str, performed_by: int, timestamp: str) -> str:
    payload = "|".join([
        previous_hash or "",
        action or "",
        str(performed_by or ""),
        timestamp or "",
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_timestamp(value: datetime) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat()


class ChainOfCustodyTracker:
    def __init__(self, db: Session):
        self.db = db

    def record_action(self, evidence_id: int, action: str, performed_by: int):
        last_record = (
            self.db.query(ChainOfCustody)
            .filter(ChainOfCustody.evidence_id == evidence_id)
            .order_by(ChainOfCustody.timestamp.desc(), ChainOfCustody.id.desc())
            .first()
        )
        previous_hash = last_record.entry_hash if last_record else None
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        entry_hash = _compute_entry_hash(previous_hash, action, performed_by, _canonical_timestamp(timestamp))

        record = ChainOfCustody(
            evidence_id=evidence_id,
            action=action,
            performed_by=performed_by,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            # Persist exactly the timestamp used to calculate entry_hash.
            timestamp=timestamp,
        )
        self.db.add(record)
        self.db.commit()
        return record

    def get_history(self, evidence_id: int):
        return self.db.query(ChainOfCustody).filter(ChainOfCustody.evidence_id == evidence_id).order_by(ChainOfCustody.timestamp.asc()).all()

    def verify_chain(self, evidence_id: int) -> dict:
        records = (
            self.db.query(ChainOfCustody)
            .filter(ChainOfCustody.evidence_id == evidence_id)
            .order_by(ChainOfCustody.timestamp.asc(), ChainOfCustody.id.asc())
            .all()
        )
        if not records:
            return {"valid": True, "records_checked": 0, "errors": []}

        errors = []
        expected_previous = None
        for record in records:
            if record.previous_hash != expected_previous:
                errors.append(f"Chain record {record.id} has broken previous_hash link")
            recalculated = _compute_entry_hash(
                record.previous_hash, record.action, record.performed_by,
                _canonical_timestamp(record.timestamp),
            )
            if record.entry_hash != recalculated:
                errors.append(f"Chain record {record.id} entry_hash mismatch")
            expected_previous = record.entry_hash

        return {
            "valid": len(errors) == 0,
            "records_checked": len(records),
            "errors": errors,
        }
