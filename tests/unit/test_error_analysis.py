import pytest
from app.services.error_analysis import compute_error_analysis


def test_error_analysis_empty_db(db_session):
    result = compute_error_analysis(db_session)
    assert result["false_positives"] == []
    assert result["false_negatives"] == []
    assert result["ambiguous_cases"] == []
    assert result["discussion"]["total_evaluated"] == 0


def test_error_analysis_structure(db_session, test_evidence):
    result = compute_error_analysis(db_session)
    assert "false_positives" in result
    assert "false_negatives" in result
    assert "ambiguous_cases" in result
    assert "discussion" in result
    discussion = result["discussion"]
    assert "total_paired" in discussion
    assert "confusion_matrix" in discussion
    assert discussion["confusion_matrix"]["tp"] >= 0
    assert discussion["confusion_matrix"]["fp"] >= 0
    assert discussion["confusion_matrix"]["fn"] >= 0
    assert discussion["confusion_matrix"]["tn"] >= 0
