SIMULATED_CASES = [
    {
        "id": "sim_001",
        "content": "I'm going to find you after school tomorrow. Watch your back.",
        "ground_truth": "not_cyberbullying",
        "category": "THREAT_LIKE_BENIGN",
        "description": "Threat-like phrasing that training data shows as non-cyberbullying"
    },
    {
        "id": "sim_002",
        "content": "you are a loser and stupid",
        "ground_truth": "cyberbullying",
        "category": "DIRECT_INSULT",
        "description": "Direct insult pattern clearly in training data"
    },
    {
        "id": "sim_003",
        "content": "Nice job failing the exam. Really smart, you are.",
        "ground_truth": "not_cyberbullying",
        "category": "SARCASM",
        "description": "Ambiguous sarcasm pattern"
    },
    {
        "id": "sim_004",
        "content": "Nobody likes you and everyone would be happier if you just disappeared.",
        "ground_truth": "cyberbullying",
        "category": "DIRECT_HARASSMENT",
        "description": "Direct harassment pattern"
    },
    {
        "id": "sim_005",
        "content": "Why is #aussietv so white? #MKR #theblock",
        "ground_truth": "not_cyberbullying",
        "category": "HASHTAG_BENIGN",
        "description": "Hashtag-heavy benign content"
    },
    {
        "id": "sim_006",
        "content": "Kill yourself",
        "ground_truth": "cyberbullying",
        "category": "EXPLICIT_THREAT",
        "description": "Explicit violent threat"
    },
    {
        "id": "sim_007",
        "content": "You're so pretty, I'd love to see you walk away from a cliff.",
        "ground_truth": "cyberbullying",
        "category": "SUBTLE_THREAT",
        "description": "Subtle/threatening compliment"
    },
    {
        "id": "sim_008",
        "content": "LOL you actually think you're good at this? Cute.",
        "ground_truth": "not_cyberbullying",
        "category": "SARCASM_BENIGN",
        "description": "Mild teasing / sarcasm without harassment"
    },
    {
        "id": "sim_009",
        "content": "People like you should be banned from the internet forever.",
        "ground_truth": "cyberbullying",
        "category": "HARASSMENT_CALL",
        "description": "Calls for exclusion/banishment"
    },
    {
        "id": "sim_010",
        "content": "I don't agree with your post, but I respect your right to share it.",
        "ground_truth": "not_cyberbullying",
        "category": "POLITE_DISAGREEMENT",
        "description": "Polite disagreement with respect"
    },
    {
        "id": "sim_011",
        "content": "You're fat and nobody will ever love you.",
        "ground_truth": "cyberbullying",
        "category": "BODY_SHAMING",
        "description": "Direct body-shaming harassment"
    },
    {
        "id": "sim_012",
        "content": "Have you considered that maybe you're the problem here?",
        "ground_truth": "not_cyberbullying",
        "category": "CONSTRUCTIVE_CRITICISM",
        "description": "Constructive criticism framed as question"
    },
    {
        "id": "sim_013",
        "content": "All [ethnicity] people are criminals and should be deported.",
        "ground_truth": "cyberbullying",
        "category": "HATE_SPEECH",
        "description": "Explicit hate speech / racism"
    },
    {
        "id": "sim_014",
        "content": "This take is garbage, but I'm not going to attack you for it.",
        "ground_truth": "not_cyberbullying",
        "category": "CRITICISM_DISENGAGED",
        "description": "Critical but disengaged comment"
    },
    {
        "id": "sim_015",
        "content": "I hope something bad happens to you and your family.",
        "ground_truth": "cyberbullying",
        "category": "MALICIOUS_WISH",
        "description": "Malicious wish of harm"
    },
]
