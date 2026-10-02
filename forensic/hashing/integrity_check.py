from forensic.hashing.sha256 import compute_sha256, verify_integrity


def check_file_integrity(file_path: str, expected_hash: str) -> bool:
    with open(file_path, "rb") as f:
        data = f.read()
    return verify_integrity(data, expected_hash)
