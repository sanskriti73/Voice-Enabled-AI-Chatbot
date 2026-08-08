"""
scripts/train_intent.py
Trains the TF-IDF + SVM intent classifier used by modules/nlu.py from
datasets/intents.json, and pickles the fitted pipeline to
models/intent_classifier.pkl.
 
Usage:
    python scripts/train_intent.py
"""
 
import json
import os
import pickle
import sys
 
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
 
 
def load_training_data(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
 
    texts, labels = [], []
    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            texts.append(pattern.lower())
            labels.append(intent["tag"])
    return texts, labels
 
 
def main():
    texts, labels = load_training_data(config.INTENTS_JSON_PATH)
 
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels if len(set(labels)) > 1 else None
    )
 
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("svm", SVC(kernel="linear", probability=True)),
    ])
    pipeline.fit(x_train, y_train)
 
    if x_test:
        predictions = pipeline.predict(x_test)
        print(classification_report(y_test, predictions))
 
    os.makedirs(os.path.dirname(config.INTENT_MODEL_PATH), exist_ok=True)
    with open(config.INTENT_MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
 
    print("Saved trained intent classifier to", config.INTENT_MODEL_PATH)
 
 
if __name__ == "__main__":
    main()

