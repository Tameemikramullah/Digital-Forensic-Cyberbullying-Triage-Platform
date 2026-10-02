from typing import Dict, Any
from forensic.evidence_processing.metadata_extractor import extract_metadata


def parse_evidence(content: str, source_platform: str, source_post_id: str) -> Dict[str, Any]:
    metadata = extract_metadata(content, source_platform, source_post_id)
    return {
        "content": content,
        "source_platform": source_platform,
        "source_post_id": source_post_id,
        "metadata": metadata,
    }
