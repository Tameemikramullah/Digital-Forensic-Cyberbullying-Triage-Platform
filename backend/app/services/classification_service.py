from typing import Tuple, Dict, Any, Optional
import os
import joblib
import numpy as np
from ..config import settings
from ml.preprocessing.cleaner import clean_text


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),  # legacy location
]


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
    raise FileNotFoundError(f"No saved model found for {model_name}")


def _load_label_encoder():
    for directory in MODEL_DIRS:
        path = os.path.join(directory, "label_encoder.pkl")
        if os.path.exists(path):
            return joblib.load(path)
    return None


def _predict(model, text: str, model_name: str = "") -> Tuple[str, float]:
    cleaned = clean_text(text)
    if model_name == "cnn" and isinstance(model, dict):
        from ml.preprocessing.tokenizer import load_tokenizer
        tokenizer_path = os.path.join(MODEL_DIRS[0], "cnn_tokenizer.json")
        if not os.path.exists(tokenizer_path):
            tokenizer_path = os.path.join(MODEL_DIRS[1], "cnn_tokenizer.json")
        if not os.path.exists(tokenizer_path):
            raise FileNotFoundError("CNN tokenizer not found")
        tokenizer_obj, _ = load_tokenizer(tokenizer_path)
        sequences = tokenizer_obj.texts_to_sequences([cleaned])
        from ml.preprocessing.tokenizer import pad_sequences
        padded = pad_sequences(sequences, maxlen=200, padding="post", truncating="post")
        proba = float(model["model"].predict(padded, verbose=0)[0][0])
        pred = "cyberbullying" if proba >= 0.5 else "not_cyberbullying"
        return pred, proba
    if model_name == "bert" and isinstance(model, dict):
        import torch
        inputs = model["tokenizer"]([cleaned], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            logits = model["model"](**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=1).numpy()[0]
        proba = float(probs.max())
        pred_idx = int(np.argmax(probs))
        pred = model["model"].config.id2label.get(pred_idx, str(pred_idx))
        return pred, proba
    proba = model.predict_proba([cleaned])[0]
    prediction = str(model.predict([cleaned])[0])
    return prediction, float(proba.max())


def classify_text(text: str, model_name: str = "svm") -> Tuple[str, float]:
    model = _load_model(model_name)
    prediction, confidence = _predict(model, text, model_name=model_name)
    label_encoder = _load_label_encoder()
    if label_encoder is not None:
        try:
            prediction = label_encoder.inverse_transform([int(prediction)])[0]
        except Exception:
            pass
    return str(prediction), confidence


def classify_text_with_explanation(text: str, model_name: str = "svm") -> Dict[str, Any]:
    model = _load_model(model_name)
    prediction, confidence = _predict(model, text, model_name=model_name)
    label_encoder = _load_label_encoder()
    if label_encoder is not None:
        try:
            prediction = label_encoder.inverse_transform([int(prediction)])[0]
        except Exception:
            pass

    explanation: Dict[str, Any] = {}
    if model_name in ["svm", "logistic", "naive_bayes"] and hasattr(model, "named_steps"):
        vectorizer = model.named_steps.get("tfidf") or model.named_steps.get("vectorizer")
        if vectorizer is not None:
            try:
                import shap
                cleaned = clean_text(text)
                X = vectorizer.transform([cleaned])
                if hasattr(model, "predict_proba"):
                    explainer = shap.Explainer(model.predict_proba, X)
                    shap_values = explainer(X)
                    vals = shap_values.values[0]
                    feature_names = vectorizer.get_feature_names_out()
                    class_idx = int(model.predict([cleaned])[0])
                    if isinstance(vals, np.ndarray) and vals.ndim > 1:
                        vals = vals[:, class_idx]
                    indices = np.argsort(np.abs(vals))[::-1][:10]
                    top_features = [
                        {"term": str(feature_names[i]), "impact": float(vals[i])} for i in indices if vals[i] != 0
                    ]
                    explanation = {"top_features": top_features, "method": "shap"}
            except Exception:
                explanation = {"top_features": [], "method": "unavailable"}

    return {
        "prediction": str(prediction),
        "confidence": confidence,
        "model_name": model_name,
        "explanation": explanation,
    }
