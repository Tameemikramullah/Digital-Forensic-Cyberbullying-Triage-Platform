import re
import string


def clean_text(text: str) -> str:
    """Normalise text while retaining signals useful for abuse detection."""
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", " urltoken ", text)
    text = re.sub(r"@\w+", " usertoken ", text)
    # Retain a hashtag's words: #StopTheHate is informative, the # is not.
    text = re.sub(r"#(\w+)", r" \1 ", text)
    # Preserve apostrophes inside words, but normalise other punctuation to space.
    text = re.sub(r"[^\w\s']", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text
