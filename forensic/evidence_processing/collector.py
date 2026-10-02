from typing import Dict, Any
from forensic.evidence_processing.parser import parse_evidence


def collect_evidence(content: str, source_platform: str, source_post_id: str) -> Dict[str, Any]:
    return parse_evidence(content, source_platform, source_post_id)
