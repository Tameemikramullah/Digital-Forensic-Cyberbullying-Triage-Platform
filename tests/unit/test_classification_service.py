import pytest
from app.services.classification_service import classify_text


def test_classify_text_returns_prediction_and_confidence():
    try:
        prediction, confidence = classify_text("This is a test message", model_name="svm")
        assert prediction is not None
        assert 0.0 <= confidence <= 1.0
    except FileNotFoundError:
        pytest.skip("Model file not found")


def test_classify_text_missing_model():
    with pytest.raises(FileNotFoundError):
        classify_text("test", model_name="nonexistent_model")
