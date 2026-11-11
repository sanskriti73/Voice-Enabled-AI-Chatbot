"""Train and persist the TF-IDF + linear SVM intent classifier."""
import json
import os
import pickle
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config


def load_training_data(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    texts, labels = [], []
    for intent in data["intents"]:
        if not intent["patterns"]:
            continue
        for pattern in intent["patterns"]:
            texts.append(pattern.lower().strip())
            labels.append(intent["tag"])

    return texts, labels


def main():
    texts, labels = load_training_data(config.INTENTS_JSON_PATH)

    if len(set(labels)) < 2:
        raise ValueError("At least two intent classes are required.")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("svm", SVC(kernel="linear", probability=True)),
    ])
    pipeline.fit(texts, labels)

    os.makedirs(config.MODELS_DIR, exist_ok=True)
    with open(config.INTENT_MODEL_PATH, "wb") as handle:
        pickle.dump(pipeline, handle)

    print(f"Trained on {len(texts)} examples across {len(set(labels))} intents.")
    print(f"Saved: {config.INTENT_MODEL_PATH}")


if __name__ == "__main__":
    main()
