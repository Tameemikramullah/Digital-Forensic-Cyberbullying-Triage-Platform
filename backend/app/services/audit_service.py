import json
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import AuditLog


def _compute_entry_hash(previous_hash: str | None, event_type: str, actor: str, event_details: str | None, created_at: str) -> str:
    payload = "|".join([
        previous_hash or "",
        event_type or "",
        actor or "",
        event_details or "",
        created_at or "",
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_timestamp(value: datetime) -> str:
    """Stable UTC-naive representation accepted by SQLite and PostgreSQL."""
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat()


def create_audit_log(db: Session, evidence_id: int, event_type: str, actor: str, event_details: dict = None):
    event_details_json = json.dumps(event_details) if event_details else None
    last_log = (
        db.query(AuditLog)
        .filter(AuditLog.evidence_id == evidence_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .first()
    )
    previous_hash = last_log.entry_hash if last_log else None
    created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    entry_hash = _compute_entry_hash(
        previous_hash, event_type, actor, event_details_json, _canonical_timestamp(created_at)
    )

    audit = AuditLog(
        evidence_id=evidence_id,
        actor=actor,
        event_type=event_type,
        event_details=event_details_json,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        # Persist exactly the timestamp that was included in the hash.
        created_at=created_at,
    )
    db.add(audit)
    db.commit()
    return audit


def verify_audit_chain(db: Session, evidence_id: int) -> dict:
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.evidence_id == evidence_id)
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        .all()
    )
    if not logs:
        return {"valid": True, "logs_checked": 0, "errors": []}

    errors = []
    expected_previous = None
    for log in logs:
        if log.previous_hash != expected_previous:
            errors.append(f"Audit log {log.id} has broken previous_hash link")
        recalculated = _compute_entry_hash(
            log.previous_hash, log.event_type, log.actor, log.event_details,
            _canonical_timestamp(log.created_at),
        )
        if log.entry_hash != recalculated:
            errors.append(f"Audit log {log.id} entry_hash mismatch")
        expected_previous = log.entry_hash

    return {
        "valid": len(errors) == 0,
        "logs_checked": len(logs),
        "errors": errors,
    }
