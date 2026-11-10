import numpy as np

from ml.evaluation.statistical_tests import mcnemar_test


def test_mcnemar_test_uses_exact_two_sided_binomial_probability():
    y_true = np.array([1, 1, 1, 1])
    pred_a = np.array([1, 1, 1, 0])
    pred_b = np.array([0, 0, 0, 1])

    result = mcnemar_test(y_true, pred_a, pred_b)

    assert result["statistic"] == 1
    assert result["p_value"] == 0.625
    assert result["a_only_correct"] == 3
    assert result["b_only_correct"] == 1
    assert result["discordant_pairs"] == 4
