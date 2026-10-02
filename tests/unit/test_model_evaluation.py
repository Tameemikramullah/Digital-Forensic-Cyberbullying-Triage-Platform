import pytest
from app.services.model_evaluation import compute_model_evaluation


def test_model_evaluation_no_data(db_session):
    result = compute_model_evaluation(db_session)
    assert result["total_evaluated"] == 0
    assert result["message"] == "No reviewed evidence with model predictions available."


def test_model_evaluation_structure(db_session, test_user):
    from app.models import Evidence, EvidenceStatus, ClassificationResult, ExaminerReview
    import datetime

    evidence = Evidence(
        evidence_hash="b" * 64,
        source_platform="Twitter",
        source_post_id="tweet_structure",
        content="Structure test content",
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

    result = compute_model_evaluation(db_session)
    assert "accuracy" in result
    assert "precision" in result
    assert "recall" in result
    assert "f1" in result
    assert "confusion_matrix" in result
