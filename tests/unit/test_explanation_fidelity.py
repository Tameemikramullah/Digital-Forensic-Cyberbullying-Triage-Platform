import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from backend.app.services.explanation_service import explain_neural_with_scorer, explain_with_model
from backend.app.services.explanation_service import generate_explanation
from ml.evaluation.explanation_fidelity import evaluate_deletion_fidelity
from ml.evaluation.explanation_fidelity import evaluate_saved_model_deletion_fidelity
from sklearn.naive_bayes import MultinomialNB


def _text_model():
    texts = [
        "kind gentle friend support",
        "nice friend kind support",
        "gentle caring friend",
        "cruel hateful attack threat",
        "hateful cruel attack",
        "threat cruel abuse",
    ]
    labels = ["safe", "safe", "safe", "harmful", "harmful", "harmful"]
    return Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(random_state=0)),
    ]).fit(texts, labels)


def test_neural_model_explanation_is_explicitly_unavailable():
    result = explain_with_model("sample text", object(), model_name="bert")

    assert result["method"] == "unavailable"
    assert result["top_features"] == []
    assert result["reason"]


def test_neural_triage_explanation_is_unavailable_when_artifact_is_missing(monkeypatch):
    import backend.app.services.classification_service as classification_service

    def missing_model(_):
        raise FileNotFoundError("No saved model found")

    monkeypatch.setattr(classification_service, "_load_model", missing_model)
    result = generate_explanation("sample text", model_name="cnn")

    assert result["method"] == "unavailable"
    assert result["reason"] == "No saved model found"


def test_neural_perturbation_explanation_scores_words_against_predicted_class():
    def scorer(text):
        texts = text if isinstance(text, list) else [text]
        results = []
        for item in texts:
            harmful_terms = sum(term in item.split() for term in ("cruel", "attack"))
            results.append([0.9 - 0.35 * harmful_terms, 0.1 + 0.35 * harmful_terms])
        return results if isinstance(text, list) else results[0]

    result = explain_neural_with_scorer(
        "cruel attack words", scorer, ["safe", "harmful"], top_k=3
    )

    assert result["method"] == "Leave-one-word-out target-class probability change"
    assert result["target_class"] == "harmful"
    assert {feature["term"] for feature in result["top_word_features"]} == {"cruel", "attack"}
    assert all(feature["impact"] > 0 for feature in result["top_word_features"])


def test_neural_fidelity_models_are_run_in_separate_framework_processes():
    with pytest.raises(ValueError, match="separate processes"):
        evaluate_saved_model_deletion_fidelity(model_names=["cnn", "bert"])


def test_deletion_fidelity_reports_probability_drop_for_top_terms():
    model = _text_model()

    result = evaluate_deletion_fidelity(
        model,
        ["cruel hateful attack threat"],
        top_k=2,
    )

    assert result["n"] == 1
    assert result["top_k"] == 2
    assert result["mean_probability_drop"] > 0
    assert result["mean_terms_deleted"] == 2
    assert "random_mean_probability_drop" in result
    assert "top_beats_random_fraction" in result


def test_logistic_explanation_uses_tfidf_weighted_coefficients():
    result = explain_with_model("cruel hateful attack", _text_model(), model_name="logistic")

    assert "TF-IDF × Logistic Regression coefficient" == result["method"]
    assert result["top_word_features"]


def test_naive_bayes_explanation_uses_log_probability_contrast():
    texts = [
        "kind gentle friend support",
        "nice friend kind support",
        "gentle caring friend",
        "cruel hateful attack threat",
        "hateful cruel attack",
        "threat cruel abuse",
    ]
    labels = ["safe", "safe", "safe", "harmful", "harmful", "harmful"]
    model = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", MultinomialNB()),
    ]).fit(texts, labels)

    result = explain_with_model("cruel hateful attack", model, model_name="naive_bayes")

    assert result["method"] == "TF-IDF × MultinomialNB log-probability contrast"
    assert result["top_word_features"]
