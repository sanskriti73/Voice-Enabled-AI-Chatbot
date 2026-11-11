"""TF-IDF + SVM NLU with deterministic lightweight entity extraction."""
import logging
import pickle
import re
import string

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

import config

logger = logging.getLogger(__name__)

for resource, path in (
    ("punkt", "tokenizers/punkt"),
    ("wordnet", "corpora/wordnet"),
    ("omw-1.4", "corpora/omw-1.4"),
):
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(resource, quiet=True)

_LEMMATIZER = WordNetLemmatizer()
_ENTITY_PATTERNS = {
    "TIME": re.compile(r"\b\d{1,2}(?::\d{2})?\s?(?:am|pm)\b", re.I),
    "DATE": re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|today|tomorrow|yesterday)\b",
        re.I,
    ),
    "NUMBER": re.compile(r"\b\d+\b"),
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
}


class NLUPipeline:
    def __init__(self, model_path=config.INTENT_MODEL_PATH):
        self.model_path = model_path
        self._classifier = None

    @property
    def classifier(self):
        if self._classifier is None:
            logger.info("Loading intent model from %s", self.model_path)
            with open(self.model_path, "rb") as handle:
                self._classifier = pickle.load(handle)
        return self._classifier

    def preprocess(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = text.translate(
            str.maketrans("", "", string.punctuation)
        )
        if not text:
            return ""
        tokens = word_tokenize(text)
        return " ".join(
            _LEMMATIZER.lemmatize(token) for token in tokens
        )

    def predict_intent(self, text: str):
        cleaned = self.preprocess(text)
        if not cleaned:
            return config.FALLBACK_INTENT, 0.0

        probabilities = self.classifier.predict_proba([cleaned])[0]
        classes = self.classifier.classes_
        best_idx = probabilities.argmax()
        intent = classes[best_idx]
        confidence = float(probabilities[best_idx])

        if confidence < config.INTENT_CONFIDENCE_THRESHOLD:
            return config.FALLBACK_INTENT, confidence

        return intent, confidence

    def extract_entities(self, text: str) -> dict:
        entities = {}
        for label, pattern in _ENTITY_PATTERNS.items():
            matches = [
                match.group().strip()
                for match in pattern.finditer(text or "")
            ]
            if matches:
                entities[label] = matches
        return entities

    def analyze(self, text: str) -> dict:
        raw_text = (text or "").strip()
        intent, confidence = self.predict_intent(raw_text)
        return {
            "raw_text": raw_text,
            "cleaned_text": self.preprocess(raw_text),
            "intent": intent,
            "confidence": confidence,
            "entities": self.extract_entities(raw_text),
        }

class NLU:
    def __init__(self):
        pass
    def process(self, text):
        return{
            "intent":"unknown",
            "confidence": 0.0,
            "entities": {}
        }    
