from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List
import joblib
import os


def build_naive_bayes_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, max_df=0.98,
            sublinear_tf=True, strip_accents="unicode",
        )),
        ("clf", MultinomialNB(alpha=0.3)),
    ])


def train_naive_bayes_model(X: List[str], y: List[int]) -> Pipeline:
    pipeline = build_naive_bayes_pipeline()
    pipeline.fit(X, y)
    return pipeline


def save_model(model, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}")
    return joblib.load(path)
