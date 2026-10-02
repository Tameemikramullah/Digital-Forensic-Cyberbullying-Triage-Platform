import csv
import json
from typing import List
from backend.app.models import AuditLog, ChainOfCustody
from sqlalchemy.orm import Session


def export_audit_to_csv(logs: List[AuditLog], file_path: str):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "evidence_id", "action", "performed_by", "details", "timestamp"])
        for log in logs:
            writer.writerow([log.id, log.evidence_id, log.action, log.performed_by, log.details_json, log.timestamp])


def export_chain_to_json(records: List[ChainOfCustody], file_path: str):
    data = [
        {
            "id": r.id,
            "evidence_id": r.evidence_id,
            "action": r.action,
            "performed_by": r.performed_by,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in records
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
