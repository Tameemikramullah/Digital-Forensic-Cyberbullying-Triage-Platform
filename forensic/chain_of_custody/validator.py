from sqlalchemy.orm import Session
from backend.app.models import ChainOfCustody
from typing import List


def validate_chain(evidence_id: int, db: Session) -> dict:
    records = db.query(ChainOfCustody).filter(ChainOfCustody.evidence_id == evidence_id).order_by(ChainOfCustody.timestamp.asc()).all()
    gaps = []
    for i in range(1, len(records)):
        prev = records[i - 1]
        curr = records[i]
        if curr.timestamp < prev.timestamp:
            gaps.append({"from": prev.id, "to": curr.id, "reason": "timestamp_regression"})
    return {"valid": len(gaps) == 0, "records": len(records), "gaps": gaps}
