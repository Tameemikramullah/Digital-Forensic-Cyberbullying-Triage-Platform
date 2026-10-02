from typing import Dict, Any
from datetime import datetime
import re


def extract_metadata(content: str, source_platform: str, source_post_id: str) -> Dict[str, Any]:
    author_match = re.search(r"@(\w+)", content)
    author_name = author_match.group(1) if author_match else None
    timestamp_match = re.search(r"\d{4}-\d{2}-\d{2}", content)
    original_timestamp = datetime.strptime(timestamp_match.group(), "%Y-%m-%d") if timestamp_match else None
    return {
        "author_name": author_name,
        "source_url": f"https://{source_platform}.com/post/{source_post_id}",
        "original_timestamp": original_timestamp.isoformat() if original_timestamp else None,
    }
