import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from ml.model_registry import run_training_pipeline

data = [
    {"text": "I hate you, you are stupid and ugly", "label": "cyberbullying"},
    {"text": "You are the worst person ever, go away", "label": "cyberbullying"},
    {"text": "Nobody likes you, just leave", "label": "cyberbullying"},
    {"text": "You are so dumb, stop talking", "label": "cyberbullying"},
    {"text": "I will make your life miserable", "label": "cyberbullying"},
    {"text": "You are a loser, everyone hates you", "label": "cyberbullying"},
    {"text": "Shut up, nobody cares what you think", "label": "cyberbullying"},
    {"text": "You are worthless and pathetic", "label": "cyberbullying"},
    {"text": "I hope something bad happens to you", "label": "cyberbullying"},
    {"text": "You are terrible at everything you do", "label": "cyberbullying"},
    {"text": "Have a nice day!", "label": "not_cyberbullying"},
    {"text": "I love this beautiful weather today", "label": "not_cyberbullying"},
    {"text": "Thanks for your help, I really appreciate it", "label": "not_cyberbullying"},
    {"text": "That was a great presentation, well done", "label": "not_cyberbullying"},
    {"text": "I enjoyed reading your article", "label": "not_cyberbullying"},
    {"text": "Let's meet tomorrow to discuss the project", "label": "not_cyberbullying"},
    {"text": "Congratulations on your new job", "label": "not_cyberbullying"},
    {"text": "The sunset looks amazing from here", "label": "not_cyberbullying"},
    {"text": "I think this is a really good idea", "label": "not_cyberbullying"},
    {"text": "Thank you for sharing this with me", "label": "not_cyberbullying"},
]

dummy_path = os.path.join(PROJECT_ROOT, "datasets", "processed", "dummy_cyberbullying.csv")
pd.DataFrame(data).to_csv(dummy_path, index=False)

result = run_training_pipeline(
    model_names=["svm", "logistic", "naive_bayes"],
    dataset_path=dummy_path,
    text_column="text",
    label_column="label",
)

print("Dummy training completed.")
for model in result["models"]:
    status = model.get("status")
    print(f"  {model['model_name']}: {status} | time={model.get('training_time_seconds', 'N/A')}s")
