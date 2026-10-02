import os
import joblib
import numpy as np
from typing import Dict, Any, List
from ml.reproducibility.test_cases import REPRODUCIBILITY_TEST_CASES
from ml.preprocessing.cleaner import clean_text


# test_runner.py lives in ml/reproducibility; two parents reach the project root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIRS = [
    os.path.join(PROJECT_ROOT, "ml", "saved_models"),
    os.path.join(PROJECT_ROOT, "saved_models"),
]


def _load_model(model_name: str = "svm"):
    for directory in MODEL_DIRS:
        path = os.path.join(directory, f"{model_name}.pkl")
        if os.path.exists(path):
            return joblib.load(path)
    raise FileNotFoundError(f"Model {model_name} not found in {MODEL_DIRS}")


def _load_label_encoder():
    for directory in MODEL_DIRS:
        path = os.path.join(directory, "label_encoder.pkl")
        if os.path.exists(path):
            return joblib.load(path)
    return None


def _get_positive_class_probability(model, text: str, label_encoder=None) -> float:
    cleaned = clean_text(text)
    proba = model.predict_proba([cleaned])[0]
    if label_encoder is not None:
        try:
            classes = label_encoder.classes_
            harmful_indices = [idx for idx, cls in enumerate(classes) if cls != "not_cyberbullying"]
            if harmful_indices:
                return float(np.sum(proba[harmful_indices]))
        except Exception:
            pass
    return float(proba.max())


def run_reproducibility_test(model_name: str = "svm") -> Dict[str, Any]:
    model = _load_model(model_name)
    label_encoder = _load_label_encoder()

    results = []
    all_passed = True
    failed_cases = []

    for case in REPRODUCIBILITY_TEST_CASES:
        cleaned = clean_text(case["input"])
        prediction = str(model.predict([cleaned])[0])
        confidence = float(model.predict_proba([cleaned])[0].max())

        if label_encoder is not None:
            try:
                prediction = label_encoder.inverse_transform([int(prediction)])[0]
            except Exception:
                pass

        predicted_flagged = prediction != "not_cyberbullying"
        expected_flagged = case["expected_flagged"]
        passed = predicted_flagged == expected_flagged
        if not passed:
            all_passed = False
            failed_cases.append({
                "id": case["id"],
                "expected_flagged": expected_flagged,
                "actual": prediction,
            })

        results.append({
            "id": case["id"],
            "input": case["input"],
            "description": case["description"],
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "expected_flagged": expected_flagged,
            "predicted_flagged": predicted_flagged,
            "passed": passed,
        })

    return {
        "model_name": model_name,
        "total_cases": len(REPRODUCIBILITY_TEST_CASES),
        "passed_cases": sum(1 for r in results if r["passed"]),
        "failed_cases_count": len(failed_cases),
        "all_passed": all_passed,
        "results": results,
        "failed_details": failed_cases,
        "reproducibility_baseline": {
            "model": model_name,
            "predictions": [r["prediction"] for r in results],
            "confidences": [r["confidence"] for r in results],
        },
    }
