import pytest
from app.services.threshold_calibration import _select_threshold, run_threshold_calibration


def test_threshold_calibration_no_reviews(db_session):
    result = run_threshold_calibration(model_name="svm", db=db_session)
    assert result["model_name"] == "svm"
    assert result.get("results", []) == []
    assert "message" in result
    assert "Target recall is 95%" in result["threshold_selection_rule"]


def test_threshold_selection_uses_highest_threshold_meeting_target_and_conservative_fallback():
    rows = [
        {"threshold": 0.5, "precision": 100.0, "recall": 50.0},
        {"threshold": 0.6, "precision": 90.0, "recall": 90.0},
        {"threshold": 0.7, "precision": 50.0, "recall": 100.0},
    ]

    assert _select_threshold(rows)["threshold"] == 0.7
    no_target_rows = [
        {"threshold": 0.5, "precision": 100.0, "recall": 50.0},
        {"threshold": 0.6, "precision": 80.0, "recall": 90.0},
        {"threshold": 0.7, "precision": 50.0, "recall": 90.0},
    ]
    assert _select_threshold(no_target_rows)["threshold"] == 0.6


def test_threshold_calibration_returns_results(db_session, test_user):
    from app.models import Evidence, EvidenceStatus, ClassificationResult, ExaminerReview
    import datetime

    evidence = Evidence(
        evidence_hash="c" * 64,
        source_platform="Twitter",
        source_post_id="tweet_cal",
        content="Calibration test content",
        acquisition_date=datetime.datetime(2026, 1, 1, 0, 0, 0),
        uploaded_by=test_user.id,
        status=EvidenceStatus.TRIAGED,
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    classification = ClassificationResult(
        evidence_id=evidence.id,
        model_name="svm",
        prediction="cyberbullying",
        confidence_score=0.8,
    )
    db_session.add(classification)

    review = ExaminerReview(
        evidence_id=evidence.id,
        examiner_id=test_user.id,
        decision="CONFIRMED",
    )
    db_session.add(review)
    db_session.commit()

    try:
        result = run_threshold_calibration(model_name="svm", db=db_session)
        assert "model_name" in result
        assert "results" in result
        assert "threshold_selection_rule" in result
        if result.get("total_reviewed", 0) > 0:
            for entry in result["results"]:
                assert "threshold" in entry
                assert "recall" in entry
                assert "precision" in entry
                assert "workload_reduction" in entry
                assert "meets_target_recall" in entry
    except FileNotFoundError:
        pytest.skip("Model file not found")
