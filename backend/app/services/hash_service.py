import hashlib
from typing import Tuple, Optional
from ..config import settings


def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_hash_from_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_hash(content: str, expected_hash: str) -> bool:
    return generate_hash(content) == expected_hash


def verify_hash_from_bytes(data: bytes, expected_hash: str) -> bool:
    return generate_hash_from_bytes(data) == expected_hash
