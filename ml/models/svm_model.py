from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from typing import List
import joblib
import os
from ml.models.text_features import build_social_media_features


def build_svm_pipeline():
    return Pipeline([
        # Keep the step name stable for the evidence-explanation service.
        ("tfidf", build_social_media_features()),
        ("clf", CalibratedClassifierCV(LinearSVC(C=1.5, class_weight="balanced"), cv=3, method="sigmoid")),
    ])


def train_svm_model(X: List[str], y: List[int]) -> Pipeline:
    pipeline = build_svm_pipeline()
    pipeline.fit(X, y)
    return pipeline


def save_model(model, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}")
    return joblib.load(path)
