from typing import Dict, List, Any


def lime_explain(text: str, model, vectorizer, num_features: int = 10) -> List[Dict[str, Any]]:
    try:
        import numpy as np
        from lime.lime_text import LimeTextExplainer

        class_names = ["non_cyberbullying", "cyberbullying"]

        def predict_proba(texts):
            X = vectorizer.transform(texts)
            if hasattr(model, "predict_proba"):
                return model.predict_proba(X)
            prob_positive = model.decision_function(X)
            prob_negative = 1 - prob_positive
            return np.vstack([prob_negative, prob_positive]).T

        explainer = LimeTextExplainer(class_names=class_names)
        exp = explainer.explain_instance(text, predict_proba, num_features=num_features)
        return [{"term": term, "impact": float(weight)} for term, weight in exp.as_list()]
    except Exception:
        return []
