import json
import os
import time
import joblib
import hashlib
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score

from ml.preprocessing.cleaner import clean_text
from ml.models.svm_model import train_svm_model
from ml.models.logistic_model import train_logistic_model
from ml.models.naive_bayes_model import train_naive_bayes_model

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
REGISTRY_PATH = os.path.join(MODEL_DIR, "model_registry.json")
DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")
MODEL_DISPLAY_NAMES = {
    "svm": "SVM",
    "logistic": "Logistic Regression",
    "naive_bayes": "Naïve Bayes",
    "cnn": "CNN",
    "bert": "DistilBERT",
}


def _ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def _load_registry() -> Dict[str, Any]:
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {"models": {}, "latest": {}}


def _save_registry(registry: Dict[str, Any]):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def _compute_dataset_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare_dataset(csv_path: str, text_column: str = "tweet_text", label_column: str = "cyberbullying_type") -> tuple:
    df = pd.read_csv(csv_path, on_bad_lines="skip")
    df = df.dropna(subset=[text_column, label_column])
    df = df[df[label_column].str.strip() != ""]
    df = df[df[label_column] != df[text_column]]
    df["cleaned_text"] = df[text_column].apply(clean_text)
    # Identical text in both partitions inflates reported performance. Keep one
    # representative deterministically before splitting.
    df = df.drop_duplicates(subset=["cleaned_text", label_column]).reset_index(drop=True)
    return df


def train_sklearn_model(model_name: str, X_train: List[str], y_train: List[int]):
    if model_name == "svm":
        return train_svm_model(X_train, y_train)
    elif model_name == "logistic":
        return train_logistic_model(X_train, y_train)
    elif model_name == "naive_bayes":
        return train_naive_bayes_model(X_train, y_train)
    raise ValueError(f"Unsupported sklearn model: {model_name}")


def train_keras_model(model_name: str, X_train: List[str], y_train: List[int], max_samples: int = None):
    if model_name == "cnn":
        from ml.models.cnn_model import train_cnn_model
        from ml.preprocessing.tokenizer import tokenize_texts
        X_seq, tokenizer = tokenize_texts(X_train)
        y_arr = np.array(y_train)
        return train_cnn_model(X_seq, y_arr), tokenizer
    elif model_name == "bert":
        from ml.models.bert_model import train_bert_model
        return train_bert_model(X_train, y_train, max_samples=max_samples, epochs=1, batch_size=32)
    raise ValueError(f"Unsupported keras model: {model_name}")


def _is_bert_available() -> bool:
    try:
        import torch  # noqa: F401
        from transformers import AutoTokenizer  # noqa: F401
        return True
    except Exception:
        return False


def _should_train_bert() -> bool:
    import os
    flag = os.environ.get("ENABLE_BERT", "0").strip().lower()
    return flag in ("1", "true", "yes", "y")


def run_training_pipeline(
    model_names: List[str] = None,
    dataset_path: str = None,
    text_column: str = "tweet_text",
    label_column: str = "cyberbullying_type",
    test_size: float = 0.2,
    random_state: int = 42,
    max_samples: int = None,
) -> Dict[str, Any]:
    _ensure_model_dir()

    if model_names is None:
        model_names = ["svm", "logistic", "naive_bayes", "cnn", "bert"]

    if dataset_path is None:
        dataset_path = os.path.join(DATASET_DIR, "raw", "cyberbullying_tweets.csv")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    if "bert" in model_names and not _is_bert_available():
        print("WARNING: DistilBERT training skipped because torch/transformers are not available.")
        model_names = [m for m in model_names if m != "bert"]

    if "bert" in model_names and not _should_train_bert():
        print("WARNING: DistilBERT training skipped because ENABLE_BERT is not set. Set ENABLE_BERT=1 to enable DistilBERT training.")
        model_names = [m for m in model_names if m != "bert"]

    df = prepare_dataset(dataset_path, text_column, label_column)
    X = df["cleaned_text"].tolist()
    y = df[label_column].tolist()
    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder().fit(y)

    from sklearn.model_selection import train_test_split
    # Stratification protects small cyberbullying categories in the final test set.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    y_train_encoded = label_encoder.transform(y_train)
    y_test_encoded = label_encoder.transform(y_test)
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, "label_encoder.pkl"))
    majority_label = label_encoder.classes_[np.bincount(y_train_encoded).argmax()]
    majority_predictions = np.full(len(y_test), majority_label, dtype=object)
    baseline_evaluation = {
        "model_name": "majority_baseline",
        "display_name": "Majority baseline",
        "train_samples": len(y_train),
        "test_samples": len(y_test),
        "majority_class": str(majority_label),
        "accuracy": round(float(accuracy_score(y_test, majority_predictions)), 4),
        "macro_f1": round(float(f1_score(y_test, majority_predictions, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_test, majority_predictions, average="weighted", zero_division=0)), 4),
        "per_class": classification_report(
            y_test,
            majority_predictions,
            labels=label_encoder.classes_.tolist(),
            target_names=label_encoder.classes_.tolist(),
            output_dict=True,
            zero_division=0,
        ),
    }

    dataset_hash = _compute_dataset_hash(dataset_path)
    timestamp = datetime.utcnow().isoformat() + "Z"
    registry = _load_registry()
    results = []

    for model_name in model_names:
        start = time.time()
        try:
            if model_name in ["svm", "logistic", "naive_bayes"]:
                model = train_sklearn_model(model_name, X_train, y_train)
                artifacts = {"model_path": os.path.join(MODEL_DIR, f"{model_name}.pkl")}
                joblib.dump(model, artifacts["model_path"])
                y_pred = model.predict(X_test)
                evaluation = {
                    "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
                    "macro_f1": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
                    "weighted_f1": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
                    "per_class": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
                }
            elif model_name in ["cnn", "bert"]:
                y_train_numeric = y_train_encoded
                y_test_numeric = y_test_encoded
                if model_name == "cnn":
                    artifacts_raw, tokenizer = train_keras_model(model_name, X_train, y_train_numeric)
                else:
                    from ml.models.bert_model import train_bert_model
                    artifacts_raw, tokenizer = train_bert_model(
                        X_train,
                        y_train_numeric.tolist(),
                        max_samples=max_samples,
                        epochs=1,
                        batch_size=32,
                        label_names=label_encoder.classes_.tolist(),
                    )
                if model_name == "cnn":
                    artifacts = {
                        "model_path": os.path.join(MODEL_DIR, "cnn_model.keras"),
                        "tokenizer_path": os.path.join(MODEL_DIR, "cnn_tokenizer.json"),
                    }
                    artifacts_raw.save(artifacts["model_path"])
                    from ml.preprocessing.tokenizer import save_tokenizer
                    save_tokenizer(tokenizer, artifacts["tokenizer_path"], max_length=200)
                else:
                    artifacts = {"model_path": os.path.join(MODEL_DIR, "bert_model")}
                    artifacts_raw.save_pretrained(artifacts["model_path"])
                    tokenizer.save_pretrained(artifacts["model_path"])
                    bert_model = artifacts_raw
                    bert_tokenizer = tokenizer

                if model_name == "cnn":
                    from ml.preprocessing.tokenizer import load_tokenizer, pad_sequences
                    tokenizer_path = os.path.join(MODEL_DIR, "cnn_tokenizer.json")
                    tokenizer_obj, max_length = load_tokenizer(tokenizer_path)
                    sequences = tokenizer_obj.texts_to_sequences(X_test)
                    padded = pad_sequences(sequences, maxlen=max_length, padding="post", truncating="post")
                    y_prob = artifacts_raw.predict(padded, verbose=0)
                    y_pred_numeric = np.argmax(y_prob, axis=1)
                else:
                    import torch
                    y_prob_batches = []
                    eval_batch_size = 32
                    with torch.no_grad():
                        for i in range(0, len(X_test), eval_batch_size):
                            batch = X_test[i:i + eval_batch_size]
                            inputs = bert_tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=128)
                            logits = bert_model(**inputs).logits
                            probs = torch.nn.functional.softmax(logits, dim=1).numpy()
                            y_prob_batches.append(probs)
                    y_prob = np.concatenate(y_prob_batches, axis=0)
                    y_pred_numeric = np.argmax(y_prob, axis=1)

                evaluation = {
                    "accuracy": round(float(accuracy_score(y_test_numeric, y_pred_numeric)), 4),
                    "macro_f1": round(float(f1_score(y_test_numeric, y_pred_numeric, average="macro", zero_division=0)), 4),
                    "weighted_f1": round(float(f1_score(y_test_numeric, y_pred_numeric, average="weighted", zero_division=0)), 4),
                    "per_class": classification_report(
                        y_test_numeric,
                        y_pred_numeric,
                        labels=np.arange(len(label_encoder.classes_)),
                        target_names=label_encoder.classes_.tolist(),
                        output_dict=True,
                        zero_division=0,
                    ),
                }
            else:
                raise ValueError(f"Unknown model: {model_name}")

            elapsed = time.time() - start
            record = {
                "model_name": model_name,
                "display_name": MODEL_DISPLAY_NAMES[model_name],
                "version": "2.0",
                "trained_at": timestamp,
                "dataset_path": dataset_path,
                "dataset_hash": dataset_hash,
                "test_size": test_size,
                "random_state": random_state,
                "training_time_seconds": round(elapsed, 3),
                "train_samples": min(max_samples, len(y_train)) if model_name == "bert" and max_samples is not None else len(y_train),
                "test_samples": len(y_test),
                "artifacts": artifacts,
                "evaluation": evaluation if model_name in ["svm", "logistic", "naive_bayes", "cnn", "bert"] else None,
                "status": "completed",
            }
            registry["models"][model_name] = record
            registry["latest"][model_name] = "2.0"
            results.append(record)
        except Exception as e:
            record = {
                "model_name": model_name,
                "display_name": MODEL_DISPLAY_NAMES[model_name],
                "version": "2.0",
                "trained_at": timestamp,
                "dataset_path": dataset_path,
                "dataset_hash": dataset_hash,
                "status": "failed",
                "error": f"{type(e).__name__}: {e}",
                "error_traceback": traceback.format_exc(),
            }
            registry["models"][model_name] = record
            results.append(record)

    _save_registry(registry)
    return {
        "dataset_info": {
            "path": dataset_path,
            "hash": dataset_hash,
            "train_samples": len(y_train),
            "test_samples": len(y_test),
            "classes": label_encoder.classes_.tolist(),
            "majority_baseline": baseline_evaluation,
        },
        "models": results,
    }


def get_model_registry() -> Dict[str, Any]:
    return _load_registry()


def get_latest_model(model_name: str) -> Optional[Dict[str, Any]]:
    registry = _load_registry()
    return registry.get("models", {}).get(model_name)


def retrain_model(model_name: str, dataset_path: str = None, **kwargs) -> Dict[str, Any]:
    result = run_training_pipeline(model_names=[model_name], dataset_path=dataset_path, **kwargs)
    return result["models"][0] if result["models"] else {}
