from scipy import stats
from sklearn.metrics import accuracy_score
from typing import Dict, List
import numpy as np


def paired_t_test(scores_a: List[float], scores_b: List[float]) -> Dict[str, float]:
    t_stat, p_value = stats.ttest_rel(scores_a, scores_b)
    return {"t_stat": float(t_stat), "p_value": float(p_value)}


def mcnemar_test(y_true, pred_a, pred_b) -> Dict[str, float]:
    a1 = np.sum((pred_a == y_true) & (pred_b == y_true))
    a2 = np.sum((pred_a == y_true) & (pred_b != y_true))
    b1 = np.sum((pred_a != y_true) & (pred_b == y_true))
    b2 = np.sum((pred_a != y_true) & (pred_b != y_true))
    discordant_pairs = int(a2 + b1)
    p_value = stats.binomtest(a2, n=discordant_pairs, p=0.5).pvalue if discordant_pairs else 1.0
    return {
        "statistic": float(min(a2, b1)),
        "p_value": float(p_value),
        "a_only_correct": float(a2),
        "b_only_correct": float(b1),
        "discordant_pairs": float(discordant_pairs),
    }
