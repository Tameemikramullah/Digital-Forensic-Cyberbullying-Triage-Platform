from typing import Tuple, Dict, Any, Optional
import os
import joblib
import numpy as np
from ..config import settings
from ml.preprocessing.cleaner import clean_text
from .explanation_service import explain_neural_with_scorer, explain_with_model


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),  # legacy location
]
CANONICAL_LABELS = {
    "age", "ethnicity", "gender", "not_cyberbullying", "other_cyberbullying", "religion"
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
                from ml.preprocessing.tokenizer import load_tokenizer
                tokenizer_path = os.path.join(directory, "cnn_tokenizer.json")
                if not os.path.exists(tokenizer_path):
                    continue
                tokenizer_obj, _ = load_tokenizer(tokenizer_path)
                return {"type": "cnn", "model": tf.keras.models.load_model(model_path), "tokenizer": tokenizer_obj}
        elif model_name in {"bert", "distilbert"}:
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


def _neural_probabilities(model, text: str, model_name: str):
    is_batch = isinstance(text, (list, tuple))
    cleaned = [clean_text(item) for item in text] if is_batch else [clean_text(text)]
    if model_name == "cnn":
        sequences = model["tokenizer"].texts_to_sequences(cleaned)
        from ml.preprocessing.tokenizer import pad_sequences
        padded = pad_sequences(sequences, maxlen=200, padding="post", truncating="post")
        probabilities = np.asarray(model["model"].predict(padded, verbose=0), dtype=float)
        return probabilities if is_batch else probabilities[0]
    import torch
    inputs = model["tokenizer"](cleaned, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        logits = model["model"](**inputs).logits
    probabilities = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()
    return probabilities if is_batch else probabilities[0]


def classify_text(text: str, model_name: str = "svm") -> Tuple[str, float]:
    model = _load_model(model_name)
    labels, probabilities = _predict_distribution(model, text, model_name)
    class_index = int(np.argmax(probabilities))
    return labels[class_index], float(probabilities[class_index])


def _predict_distribution(model, text: str, model_name: str):
    """Return class labels and probabilities in the shared dataset label order."""
    cleaned = clean_text(text)
    label_encoder = _load_label_encoder()
    if model_name == "cnn" and isinstance(model, dict):
        sequences = model["tokenizer"].texts_to_sequences([cleaned])
        from ml.preprocessing.tokenizer import pad_sequences
        padded = pad_sequences(sequences, maxlen=200, padding="post", truncating="post")
        probabilities = np.asarray(model["model"].predict(padded, verbose=0)[0], dtype=float)
        labels = list(label_encoder.classes_) if label_encoder is not None else [str(i) for i in range(len(probabilities))]
    elif model_name in {"bert", "distilbert"} and isinstance(model, dict):
        import torch
        inputs = model["tokenizer"]([cleaned], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            logits = model["model"](**inputs).logits
        probabilities = torch.nn.functional.softmax(logits, dim=1).cpu().numpy()[0]
        id2label = model["model"].config.id2label
        labels = [str(id2label[index]) for index in sorted(id2label)]
        generic_labels = all(label.isdigit() or (label.startswith("LABEL_") and label[6:].isdigit()) for label in labels)
        if label_encoder is not None and generic_labels:
            labels = [str(label) for label in label_encoder.classes_]
        if label_encoder is not None and labels != [str(label) for label in label_encoder.classes_]:
            raise RuntimeError("DistilBERT label mapping does not match the shared label encoder")
    else:
        probabilities = np.asarray(model.predict_proba([cleaned])[0], dtype=float)
        labels = [str(label) for label in model.classes_]
        if label_encoder is not None:
            try:
                labels = list(label_encoder.inverse_transform([int(label) for label in labels]))
            except (TypeError, ValueError):
                pass

    labels = [str(label) for label in labels]
    if len(labels) != len(probabilities):
        raise RuntimeError(f"{model_name} output labels do not match its probability vector")
    if set(labels) != CANONICAL_LABELS:
        raise RuntimeError(f"{model_name} does not use the shared six-class label space")
    return labels, probabilities


def classify_text_with_scores(text: str, model_name: str = "svm") -> Dict[str, Any]:
    """Return top-class confidence and probability mass across harmful classes."""
    model = _load_model(model_name)
    labels, probabilities = _predict_distribution(model, text, model_name)
    class_index = int(np.argmax(probabilities))
    return {
        "prediction": str(labels[class_index]),
        "confidence": float(probabilities[class_index]),
        "risk_score": float(sum(probability for label, probability in zip(labels, probabilities) if label != "not_cyberbullying")),
    }


def classify_text_with_explanation(text: str, model_name: str = "svm") -> Dict[str, Any]:
    model = _load_model(model_name)
    labels, probabilities = _predict_distribution(model, text, model_name)
    class_index = int(np.argmax(probabilities))
    prediction = labels[class_index]
    confidence = float(probabilities[class_index])
    label_encoder = _load_label_encoder()

    if model_name in {"cnn", "bert", "distilbert"}:
        label_encoder = _load_label_encoder()
        if label_encoder is not None:
            class_labels = list(label_encoder.classes_)
        elif model_name in {"bert", "distilbert"}:
            id2label = model["model"].config.id2label
            class_labels = [id2label[index] for index in sorted(id2label)]
        else:
            class_labels = [str(index) for index in range(int(model["model"].output_shape[-1]))]
        explanation = explain_neural_with_scorer(
            text,
            lambda candidate: _neural_probabilities(model, candidate, model_name),
            class_labels,
        )
    else:
        explanation = explain_with_model(text, model, model_name=model_name)

    return {
        "prediction": str(prediction),
        "confidence": confidence,
        "model_name": model_name,
        "explanation": explanation,
    }
