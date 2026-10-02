import os
import time
import joblib
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sklearn.metrics import f1_score
from ..models import Evidence, ExaminerReview
from ml.preprocessing.cleaner import clean_text
from ml.preprocessing.tokenizer import pad_sequences

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),  # legacy location
]

EXPLAINABILITY_SCORES = {
    "svm": "High",
    "logistic": "High",
    "naive_bayes": "Medium",
    "cnn": "Medium",
    "bert": "Lower",
}

RUNTIME_CLASSES = {
    "svm": "Fast",
    "logistic": "Fast",
    "naive_bayes": "Fast",
    "cnn": "Medium",
    "bert": "Slow",
}


def _load_model(model_name: str):
    for directory in MODEL_DIRS:
        if model_name in ["svm", "logistic", "naive_bayes"]:
            path = os.path.join(directory, f"{model_name}.pkl")
            if os.path.exists(path):
                return joblib.load(path)
        elif model_name == "cnn":
            model_path = os.path.join(directory, "cnn_model.keras")
            if os.path.exists(model_path):
                import tensorflow as tf
                return {"type": "cnn", "model": tf.keras.models.load_model(model_path)}
        elif model_name == "bert":
            model_path = os.path.join(directory, "bert_model")
            if os.path.exists(model_path):
                os.environ["CUDA_VISIBLE_DEVICES"] = ""
                import torch
                torch.set_num_threads(4)
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSequenceClassification.from_pretrained(model_path)
                model = model.to("cpu").eval()
                return {"type": "bert", "model": model, "tokenizer": tokenizer}
    return None


def _get_evidence_with_reviews(db: Session) -> List[tuple]:
    return (
        db.query(Evidence, ExaminerReview)
        .join(ExaminerReview, Evidence.id == ExaminerReview.evidence_id)
        .filter(ExaminerReview.decision.in_(["CONFIRMED", "REJECTED"]))
        .all()
    )


def _predict(model, text: str, model_name: str = "") -> tuple:
    cleaned = clean_text(text)
    if model_name == "cnn" and isinstance(model, dict):
        from ml.preprocessing.tokenizer import load_tokenizer
        tokenizer_path = os.path.join(MODEL_DIRS[0], "cnn_tokenizer.json")
        if not os.path.exists(tokenizer_path):
            raise FileNotFoundError("CNN tokenizer not found")
        tokenizer, _ = load_tokenizer(tokenizer_path)
        sequences = tokenizer.texts_to_sequences([cleaned])
        padded = pad_sequences(sequences, maxlen=200, padding="post", truncating="post")
        proba = float(model["model"].predict(padded, verbose=0)[0][0])
        pred = 1 if proba >= 0.5 else 0
        return pred, proba
    if model_name == "bert" and isinstance(model, dict):
        import torch
        inputs = model["tokenizer"]([cleaned], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            logits = model["model"](**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=1).numpy()[0]
        proba = float(probs.max())
        pred = int(np.argmax(probs))
        return pred, proba
    proba = model.predict_proba([cleaned])[0]
    prediction = str(model.predict([cleaned])[0])
    is_flagged = int(prediction != "not_cyberbullying")
    return is_flagged, float(proba.max())


def run_inter_model_comparison(db: Session, model_names: List[str] = None) -> Dict[str, Any]:
    if model_names is None:
        model_names = ["svm", "logistic", "naive_bayes", "cnn", "bert"]

    evidence_reviews = _get_evidence_with_reviews(db)

    if not evidence_reviews:
        return {
            "models": [],
            "message": "No reviewed evidence available for comparison.",
        }

    y_true = []
    texts = []
    for evidence, review in evidence_reviews:
        y_true.append(1 if review.decision == "CONFIRMED" else 0)
        texts.append(evidence.content)

    y_true = np.array(y_true)
    total_pairs = len(y_true)

    MIN_SAMPLE_SIZE = 10
    small_sample_warning = total_pairs < MIN_SAMPLE_SIZE
    perfect_score_warning = False

    results = []

    for model_name in model_names:
        model = _load_model(model_name)
        if model is None:
            artifact_error = "No trained compatible model artifact found"
            if model_name in ["cnn", "bert"]:
                artifact_error = "TensorFlow is not installed in the backend environment; CNN/BERT artifacts cannot be loaded or compared"
            results.append({
                "model": model_name,
                "f1": None,
                "runtime": RUNTIME_CLASSES.get(model_name, "Unknown"),
                "explainability": EXPLAINABILITY_SCORES.get(model_name, "Unknown"),
                "selected": False,
                "error": artifact_error,
                "warning": None,
            })
            continue

        start = time.time()
        y_pred = []
        for text in texts:
            try:
                pred, _ = _predict(model, text)
                y_pred.append(pred)
            except Exception:
                y_pred.append(0)
        elapsed_ms = (time.time() - start) * 1000

        avg_runtime_ms = elapsed_ms / len(texts) if texts else 0
        runtime_class = "Fast" if avg_runtime_ms < 50 else "Medium" if avg_runtime_ms < 500 else "Slow"

        f1 = float(f1_score(y_true, np.array(y_pred), zero_division=0))
        f1_pct = round(f1 * 100, 2)

        warnings = []
        if small_sample_warning:
            warnings.append(
                f"Small sample size ({total_pairs} reviewed items). Operational F1 may not be statistically reliable."
            )
        if f1_pct == 100.0:
            perfect_score_warning = True
            warnings.append(
                "Perfect operational F1 (100%) is suspicious. This may indicate data leakage, overfitting, or an overly trivial reviewed set."
            )

        results.append({
            "model": model_name,
            "f1": f1_pct,
            "runtime": runtime_class,
            "avg_runtime_ms": round(avg_runtime_ms, 2),
            "explainability": EXPLAINABILITY_SCORES.get(model_name, "Unknown"),
            "selected": model_name == "svm",
            "warning": " | ".join(warnings) if warnings else None,
        })

    selected = next((r for r in results if r["selected"]), None)
    justification = (
        "SVM selected for operational triage due to coefficient-based explainability, deterministic runtime, "
        "and strong held-out multiclass performance. The displayed F1 is the separate binary operational "
        "agreement score against examiner decisions, not the model's held-out macro-F1."
        if selected else "No model selected."
    )

    global_warnings = []
    if small_sample_warning:
        global_warnings.append(
            f"Global warning: only {total_pairs} reviewed evidence items are available. "
            "Collect more examiner-reviewed cases before using these operational metrics for publication."
        )
    if perfect_score_warning:
        global_warnings.append(
            "Global warning: one or more models achieved 100% operational F1. "
            "Investigate possible data leakage, training/test overlap, or dataset bias before citing these results."
        )

    return {
        "models": results,
        "selected_model": selected["model"] if selected else None,
        "justification": justification,
        "warnings": global_warnings,
        "meta": {
            "total_reviewed_pairs": total_pairs,
            "small_sample_warning": small_sample_warning,
            "perfect_score_warning": perfect_score_warning,
        },
    }
