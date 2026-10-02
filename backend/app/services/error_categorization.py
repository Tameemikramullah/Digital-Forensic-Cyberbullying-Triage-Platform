FORENSIC_ERROR_CATEGORIES = {
    "SARCASM": {
        "keywords": ["sarcasm", "sarcastic", "irony", "ironic", "facetious", "dry humor", "dry humour"],
        "description": "Content uses sarcasm or ironic language that was misinterpreted as abusive",
    },
    "MISSING_CONTEXT": {
        "keywords": ["context", "missing context", "out of context", "lack of context", "ambiguous context", "unclear context"],
        "description": "Classification failed because necessary context was absent or unavailable",
    },
    "SLANG_INFORMAL": {
        "keywords": ["slang", "informal", "colloquial", "idiom", "idiomatic", "vernacular", "casual language"],
        "description": "Informal language, slang, or idiomatic expressions misclassified as harmful",
    },
    "ANNOTATION_AMBIGUITY": {
        "keywords": ["annotation ambiguity", "labeling ambiguity", "label ambiguity", "coding ambiguity", "annotator disagreement", "inter-annotator"],
        "description": "Ground-truth labeling was ambiguous or inconsistent between annotators",
    },
    "IDENTITY_TERMS": {
        "keywords": ["identity", "race", "gender", "religion", "ethnicity", "age", "disability", "sexual orientation", "protected class"],
        "description": "Error involves identity-based terms where classification sensitivity is critical",
    },
    "SUBTLE_HARASSMENT": {
        "keywords": ["subtle", "implicit", "covert", "coded", "passive-aggressive", "microaggression"],
        "description": "Harassment was present but expressed in a subtle or coded manner",
    },
    "EXPLICIT_THREAT": {
        "keywords": ["explicit threat", "direct threat", "physical threat", "violence", "harm", "danger"],
        "description": "Content contains explicit threats or violent language",
    },
    "CROSS_PLATFORM": {
        "keywords": ["platform", "twitter", "facebook", "instagram", "tiktok", "youtube", "social media"],
        "description": "Error may be influenced by platform-specific norms or formatting",
    },
}


def categorize_error(review_notes: str | None, content: str | None, prediction: str | None, examiner_decision: str | None) -> list[str]:
    text = " ".join(filter(None, [review_notes or "", content or "", prediction or "", examiner_decision or ""])).lower()
    matched = []
    for category, info in FORENSIC_ERROR_CATEGORIES.items():
        if any(keyword in text for keyword in info["keywords"]):
            matched.append(category)
    if not matched:
        matched.append("UNCATEGORIZED")
    return matched
