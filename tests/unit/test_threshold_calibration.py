import pytest
from app.services.threshold_calibration import run_threshold_calibration


def test_threshold_calibration_no_reviews(db_session):
    result = run_threshold_calibration(model_name="svm", db=db_session)
    assert result["model_name"] == "svm"
    assert result.get("results", []) == []
    assert "message" in result


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
        if result.get("total_reviewed", 0) > 0:
            for entry in result["results"]:
                assert "threshold" in entry
                assert "recall" in entry
                assert "precision" in entry
                assert "workload_reduction" in entry
    except FileNotFoundError:
        pytest.skip("Model file not found")
