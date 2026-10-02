REPRODUCIBILITY_TEST_CASES = [
    {
        "id": "rep_001",
        "input": "I'm going to find you after school tomorrow. Watch your back.",
        "expected_flagged": False,
        "expected_confidence_range": [0.0, 1.0],
        "description": "Threat-like phrasing that training data shows as non-cyberbullying"
    },
    {
        "id": "rep_002",
        "input": "you are a loser and stupid",
        "expected_flagged": True,
        "expected_confidence_range": [0.0, 1.0],
        "description": "Direct insult pattern"
    },
    {
        "id": "rep_003",
        "input": "Nice job failing the exam. Really smart, you are.",
        "expected_flagged": False,
        "expected_confidence_range": [0.0, 1.0],
        "description": "Ambiguous sarcasm pattern"
    },
    {
        "id": "rep_004",
        "input": "Nobody likes you and everyone would be happier if you just disappeared.",
        "expected_flagged": True,
        "expected_confidence_range": [0.0, 1.0],
        "description": "Direct harassment pattern"
    },
    {
        "id": "rep_005",
        "input": "Why is #aussietv so white? #MKR #theblock",
        "expected_flagged": False,
        "expected_confidence_range": [0.0, 1.0],
        "description": "Hashtag-heavy benign content"
    },
]
