from app.models import RepeatabilityTest
from app.services import repeatability_service


def test_repeatability_records_identical_predictions_and_explanations(db_session, evidence, monkeypatch):
    monkeypatch.setattr(
        repeatability_service,
        "classify_text",
        lambda text, model_name: ("gender", 0.81),
    )
    monkeypatch.setattr(
        repeatability_service,
        "generate_explanation",
        lambda text, model_name: {"top_features": [{"term": "worthless", "impact": 0.42}]},
    )

    result = repeatability_service.run_repeatability_test(
        db_session, evidence.id, iterations=3
    )
    assert result["pass_fail"] == "PASS"
    assert result["prediction_consistency"] == 100.0
    assert result["explanation_consistency"] == 100.0
    assert db_session.query(RepeatabilityTest).one().iterations == 3
