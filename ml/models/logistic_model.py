from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from typing import List
import joblib
import os
from ml.models.text_features import build_social_media_features


def build_logistic_pipeline():
    return Pipeline([
        # Keep the step name stable for the evidence-explanation service.
        ("tfidf", build_social_media_features()),
        ("clf", LogisticRegression(C=4.0, max_iter=2_000, class_weight="balanced", solver="saga", n_jobs=-1)),
    ])


def train_logistic_model(X: List[str], y: List[int]) -> Pipeline:
    pipeline = build_logistic_pipeline()
    pipeline.fit(X, y)
    return pipeline


def save_model(model, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}")
    return joblib.load(path)
