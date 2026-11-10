import pytest
from sklearn.preprocessing import LabelEncoder

from backend.app.api.triage import _check_model_agreement, _compute_risk, _plurality_vote
from backend.app.services.classification_service import _predict_distribution


def test_plurality_uses_one_equal_vote_per_successful_model():
    votes = [
        {"prediction": "religion", "confidence": 0.99},
        {"prediction": "age", "confidence": 0.51},
        {"prediction": "age", "confidence": 0.50},
        {"prediction": "error", "confidence": 0.0},
    ]

    result = _plurality_vote(votes)

    assert result["prediction"] == "age"
    assert result["confidence"] == pytest.approx(2 / 3)
    assert result["risk_score"] == pytest.approx(1.0)
    assert result["valid_votes"] == 3


def test_plurality_risk_score_is_harmful_vote_share():
    votes = [
        {"prediction": "not_cyberbullying", "confidence": 0.99},
        {"prediction": "age", "confidence": 0.51},
        {"prediction": "not_cyberbullying", "confidence": 0.50},
        {"prediction": "unrecognized_label", "confidence": 1.0},
    ]

    result = _plurality_vote(votes)

    assert result["risk_score"] == pytest.approx(1 / 3)
    assert result["confidence"] == pytest.approx(2 / 3)


@pytest.mark.parametrize(
    ("score", "threshold", "expected"),
    [
        (0.49, 0.5, ("LOW", False)),
        (0.50, 0.5, ("MEDIUM", True)),
        (0.79, 0.5, ("MEDIUM", True)),
        (0.80, 0.5, ("HIGH", True)),
        (0.89, 0.9, ("LOW", False)),
        (0.90, 0.9, ("HIGH", True)),
    ],
)
def test_risk_level_boundaries(score, threshold, expected):
    assert _compute_risk(score, threshold) == expected


def test_label_tie_forces_review_without_comparing_confidences():
    votes = [
        {"prediction": "age", "confidence": 0.99},
        {"prediction": "religion", "confidence": 0.51},
    ]

    result = _check_model_agreement(votes)

    assert result["tie"] is True
    assert result["forced_review"] is True
    assert result["winning_vote_share"] == pytest.approx(0.5)


def test_missing_risk_score_is_unknown_and_requires_review():
    assert _compute_risk(None) == ("UNKNOWN", True)


def test_binary_model_output_is_rejected_against_six_class_encoder(monkeypatch):
    encoder = LabelEncoder().fit([
        "age", "ethnicity", "gender", "not_cyberbullying", "other_cyberbullying", "religion"
    ])

    class BinaryModel:
        classes_ = [0, 1]

        def predict_proba(self, _texts):
            return [[0.6, 0.4]]

    monkeypatch.setattr(
        "backend.app.services.classification_service._load_label_encoder", lambda: encoder
    )
    with pytest.raises(RuntimeError, match="shared six-class label space"):
        _predict_distribution(BinaryModel(), "text", "svm")
