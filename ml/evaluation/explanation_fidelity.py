import re
import os
from typing import Any, Dict, List

import joblib
import numpy as np

from backend.app.services.explanation_service import explain_with_model
from ml.preprocessing.cleaner import clean_text


def _delete_terms(text: str, terms: List[str]) -> str:
    deleted_text = text
    for term in terms:
        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
        deleted_text = re.sub(pattern, " ", deleted_text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", deleted_text).strip()


def _fidelity_summary(drops, random_drops, top_k):
    result = {
        "n": len(drops),
        "top_k": top_k,
        "mean_probability_drop": float(np.mean(drops)),
        "median_probability_drop": float(np.median(drops)),
        "positive_drop_fraction": float(np.mean(np.asarray(drops) > 0)),
    }
    if random_drops:
        paired_top = np.asarray(drops[:len(random_drops)])
        paired_random = np.asarray(random_drops)
        result.update({
            "random_control_n": len(random_drops),
            "random_mean_probability_drop": float(np.mean(paired_random)),
            "top_beats_random_fraction": float(np.mean(paired_top > paired_random)),
            "paired_mean_advantage": float(np.mean(paired_top - paired_random)),
        })
    return result


def evaluate_deletion_fidelity(
    model,
    texts: List[str],
    top_k: int = 3,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Compare attributed-word deletion with deleting the same number of random words."""
    probability_drops = []
    random_probability_drops = []
    paired_probability_drops = []
    original_probabilities = []
    deleted_probabilities = []
    deleted_term_counts = []
    rng = np.random.RandomState(random_state)

    for text in texts:
        cleaned = clean_text(text)
        prediction = model.predict([cleaned])[0]
        explanation = explain_with_model(cleaned, model, model_name="linear")
        terms = []
        for feature in explanation.get("top_word_features", []):
            if feature["impact"] <= 0:
                continue
            term = feature["term"]
            if term not in terms:
                terms.append(term)
            if len(terms) == top_k:
                break
        if not terms:
            continue

        deleted_text = _delete_terms(cleaned, terms)
        if deleted_text == cleaned:
            continue

        probabilities = model.predict_proba([cleaned, deleted_text])
        class_index = list(model.classes_).index(prediction)
        original_probability = float(probabilities[0, class_index])
        deleted_probability = float(probabilities[1, class_index])
        original_probabilities.append(original_probability)
        deleted_probabilities.append(deleted_probability)
        probability_drops.append(original_probability - deleted_probability)
        deleted_term_counts.append(len(terms))

        candidates = list(dict.fromkeys(re.findall(r"(?u)\b\w+\b", cleaned)))
        candidates = [candidate for candidate in candidates if candidate not in terms]
        if candidates:
            random_terms = rng.choice(candidates, size=min(len(terms), len(candidates)), replace=False).tolist()
            random_text = _delete_terms(cleaned, random_terms)
            random_probabilities = model.predict_proba([random_text])[0]
            random_probability_drops.append(
                original_probability - float(random_probabilities[class_index])
            )
            paired_probability_drops.append(original_probability - deleted_probability)

    if not probability_drops:
        return {"n": 0, "top_k": top_k, "error": "No examples had deletable attributed terms."}

    result = _fidelity_summary(paired_probability_drops, random_probability_drops, top_k)
    result["n"] = len(probability_drops)
    result["mean_probability_drop"] = float(np.mean(probability_drops))
    result["median_probability_drop"] = float(np.median(probability_drops))
    result["positive_drop_fraction"] = float(np.mean(np.asarray(probability_drops) > 0))
    result.update({
        "mean_original_probability": float(np.mean(original_probabilities)),
        "mean_deleted_probability": float(np.mean(deleted_probabilities)),
        "mean_terms_deleted": float(np.mean(deleted_term_counts)),
    })
    return result


def evaluate_saved_model_deletion_fidelity(
    model_names: List[str] = None,
    sample_size: int = 500,
    random_state: int = 42,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Reproduce deletion-fidelity metrics on the shared held-out test split."""
    from sklearn.model_selection import train_test_split
    from ml.model_registry import DATASET_DIR, MODEL_DIR, prepare_dataset

    model_names = model_names or ["svm", "logistic", "naive_bayes"]
    requested_neural = {"bert" if name == "distilbert" else name for name in model_names} & {"cnn", "bert"}
    if len(requested_neural) > 1:
        raise ValueError("Evaluate CNN and DistilBERT in separate processes; TensorFlow and PyTorch runtimes conflict in this environment.")
    dataset_path = os.path.join(DATASET_DIR, "raw", "cyberbullying_tweets.csv")
    dataset = prepare_dataset(dataset_path)
    texts = dataset["cleaned_text"].tolist()
    labels = dataset["cyberbullying_type"].tolist()
    _, test_texts, _, _ = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    sample_indices = np.random.RandomState(random_state).choice(
        len(test_texts), size=min(sample_size, len(test_texts)), replace=False
    )
    sample_texts = [test_texts[index] for index in sample_indices]
    model_results = {}
    neural_names = {"cnn", "bert", "distilbert"}
    for model_name in model_names:
        if model_name in neural_names:
            from backend.app.services.classification_service import (
                _load_model,
                _load_label_encoder,
                _neural_probabilities,
            )
            from backend.app.services.explanation_service import explain_neural_with_scorer

            normalized_name = "bert" if model_name == "distilbert" else model_name
            try:
                model = _load_model(normalized_name)
            except FileNotFoundError as error:
                model_results[model_name] = {"n": 0, "error": str(error)}
                continue
            label_encoder = _load_label_encoder()
            if label_encoder is not None:
                class_labels = list(label_encoder.classes_)
            elif normalized_name == "bert":
                id2label = model["model"].config.id2label
                class_labels = [id2label[index] for index in sorted(id2label)]
            else:
                class_labels = [str(index) for index in range(int(model["model"].output_shape[-1]))]

            drops, random_drops, paired_drops, original, deleted = [], [], [], [], []
            rng = np.random.RandomState(random_state)
            scorer = lambda candidate: _neural_probabilities(model, candidate, normalized_name)
            for text in sample_texts:
                cleaned = clean_text(text)
                probabilities = np.asarray(scorer(cleaned), dtype=float)
                target_index = int(np.argmax(probabilities))
                explanation = explain_neural_with_scorer(
                    cleaned, scorer, class_labels, top_k=top_k
                )
                terms = [
                    feature["term"] for feature in explanation.get("top_word_features", [])
                    if feature["impact"] > 0
                ][:top_k]
                if not terms:
                    continue
                deleted_text = _delete_terms(cleaned, terms)
                if deleted_text == cleaned:
                    continue
                after = np.asarray(scorer(deleted_text), dtype=float)
                original.append(float(probabilities[target_index]))
                deleted.append(float(after[target_index]))
                drops.append(float(probabilities[target_index] - after[target_index]))
                candidates = list(dict.fromkeys(re.findall(r"(?u)\b\w+\b", cleaned)))
                candidates = [candidate for candidate in candidates if candidate not in terms]
                if candidates:
                    random_terms = rng.choice(candidates, size=min(len(terms), len(candidates)), replace=False).tolist()
                    random_text = _delete_terms(cleaned, random_terms)
                    random_probabilities = np.asarray(scorer(random_text), dtype=float)
                    random_drops.append(
                        float(probabilities[target_index] - random_probabilities[target_index])
                    )
                    paired_drops.append(float(probabilities[target_index] - after[target_index]))

            if drops:
                model_result = _fidelity_summary(paired_drops, random_drops, top_k)
                model_result["n"] = len(drops)
                model_result["mean_probability_drop"] = float(np.mean(drops))
                model_result["median_probability_drop"] = float(np.median(drops))
                model_result["positive_drop_fraction"] = float(np.mean(np.asarray(drops) > 0))
                model_result.update({
                    "mean_original_probability": float(np.mean(original)),
                    "mean_deleted_probability": float(np.mean(deleted)),
                })
                model_results[model_name] = model_result
            else:
                model_results[model_name] = {
                    "n": 0,
                    "top_k": top_k,
                    "error": "No examples had deletable positively attributed words.",
                }
        else:
            model_path = os.path.join(MODEL_DIR, f"{model_name}.pkl")
            if not os.path.exists(model_path):
                model_results[model_name] = {"n": 0, "error": f"Model artifact not found: {model_path}"}
                continue
            model = joblib.load(model_path)
            model_results[model_name] = evaluate_deletion_fidelity(
                model, sample_texts, top_k=top_k, random_state=random_state
            )

    return {
        "test_size": len(test_texts),
        "sample_size": len(sample_texts),
        "sample_seed": random_state,
        "top_k": top_k,
        "models": model_results,
    }
