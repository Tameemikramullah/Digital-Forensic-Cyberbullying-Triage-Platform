from typing import Dict, List, Any
from ml.explainability.attribution import compute_attribution_scores
from ml.explainability.lime_analysis import lime_explain


def shap_analysis(text: str, model, vectorizer) -> Dict[str, Any]:
    top_features = compute_attribution_scores(text, model, vectorizer)
    return {"method": "shap", "top_features": top_features}


def combined_explanation(text: str, model, vectorizer) -> Dict[str, Any]:
    shap_features = compute_attribution_scores(text, model, vectorizer)
    lime_features = lime_explain(text, model, vectorizer)
    return {
        "shap": shap_features,
        "lime": lime_features,
        "top_features": shap_features[:5],
    }
