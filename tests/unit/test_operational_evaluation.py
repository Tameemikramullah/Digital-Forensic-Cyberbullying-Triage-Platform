import pytest
from app.services.operational_evaluation import compute_operational_metrics


def test_operational_metrics_empty_db(db_session):
    result = compute_operational_metrics(db_session)
    assert result["total_evidence"] == 0
    assert result["flagged"] == 0
    assert result["true_positives"] == 0
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["true_negatives"] == 0


def test_operational_metrics_structure(db_session, test_evidence):
    result = compute_operational_metrics(db_session)
    required_keys = [
        "total_evidence", "triaged", "reviewed", "flagged",
        "confirmed", "rejected", "escalated",
        "true_positives", "false_positives", "false_negatives", "true_negatives",
        "total_paired", "recall", "precision",
        "false_positive_rate", "false_negative_rate",
        "workload_reduction", "triage_reduction",
    ]
    for key in required_keys:
        assert key in result
