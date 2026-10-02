import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from ml.model_registry import run_training_pipeline

result = run_training_pipeline(
    model_names=["svm", "logistic", "naive_bayes", "cnn", "bert"],
    dataset_path=os.path.join(PROJECT_ROOT, "datasets", "raw", "cyberbullying_tweets.csv"),
)

print("Training completed.")
for model in result["models"]:
    status = model.get("status")
    error = model.get("error")
    print(f"  {model['model_name']}: {status} | time={model.get('training_time_seconds', 'N/A')}s")
    if error:
        print(f"    error: {error}")
