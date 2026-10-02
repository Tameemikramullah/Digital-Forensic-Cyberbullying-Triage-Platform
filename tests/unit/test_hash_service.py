from app.services.hash_service import generate_hash, verify_hash


def test_hash_is_deterministic_and_sha256_sized():
    content = "An evidential social-media post"
    assert generate_hash(content) == generate_hash(content)
    assert len(generate_hash(content)) == 64


def test_hash_changes_when_content_changes():
    original = generate_hash("original content")
    assert not verify_hash("altered content", original)
    assert verify_hash("original content", original)
