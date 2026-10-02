from typing import Dict, List, Any


def compute_attribution_scores(text: str, model, vectorizer) -> List[Dict[str, Any]]:
    try:
        import shap
        import numpy as np

        X = vectorizer.transform([text])
        explainer = shap.Explainer(model.predict_proba, X)
        shap_values = explainer(X)
        vals = shap_values.values[0]
        feature_names = vectorizer.get_feature_names_out()
        class_idx = int(model.predict([text])[0])
        if isinstance(vals, np.ndarray) and vals.ndim > 1:
            vals = vals[:, class_idx]
        indices = np.argsort(np.abs(vals))[::-1][:10]
        return [{"term": str(feature_names[i]), "impact": float(vals[i])} for i in indices if vals[i] != 0]
    except Exception:
        return []
