from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt
from typing import Tuple
import numpy as np


def compute_calibration(y_true, y_prob, n_bins: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
    return prob_true, prob_pred


def plot_calibration_curve(y_true, y_prob, save_path: str = None):
    prob_true, prob_pred = compute_calibration(y_true, y_prob)
    plt.figure()
    plt.plot(prob_pred, prob_true, marker="o", label="Model")
    plt.plot([0, 1], [0, 1], linestyle="--", label="Perfectly calibrated")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.legend()
    if save_path:
        plt.savefig(save_path)
    plt.close()
