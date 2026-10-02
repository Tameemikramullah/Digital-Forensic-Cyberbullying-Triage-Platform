from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


def compute_confusion_matrix(y_true, y_pred):
    return confusion_matrix(y_true, y_pred)


def plot_confusion_matrix(y_true, y_pred, labels=None, save_path: str = None):
    cm = compute_confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    if save_path:
        plt.savefig(save_path)
    plt.close()
