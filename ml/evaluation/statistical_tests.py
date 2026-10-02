from scipy import stats
from sklearn.metrics import accuracy_score
from typing import Dict, List
import numpy as np


def paired_t_test(scores_a: List[float], scores_b: List[float]) -> Dict[str, float]:
    t_stat, p_value = stats.ttest_rel(scores_a, scores_b)
    return {"t_stat": float(t_stat), "p_value": float(p_value)}


def mcnemar_test(y_true, pred_a, pred_b) -> Dict[str, float]:
    from statsmodels.stats.contingency_tables import mcnemar
    a1 = np.sum((pred_a == y_true) & (pred_b == y_true))
    a2 = np.sum((pred_a == y_true) & (pred_b != y_true))
    b1 = np.sum((pred_a != y_true) & (pred_b == y_true))
    b2 = np.sum((pred_a != y_true) & (pred_b != y_true))
    table = [[a1, a2], [b1, b2]]
    result = mcnemar(table, exact=True)
    return {"statistic": float(result.statistic), "p_value": float(result.pvalue)}
