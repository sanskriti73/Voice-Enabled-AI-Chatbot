"""
modules/nlu.py
Natural Language Understanding pipeline.
 
Stages:
    1. Text pre-processing (lowercase, punctuation strip, tokenize, lemmatize).
    2. Intent classification using a pre-trained TF-IDF + SVM pipeline
       (models/intent_classifier.pkl, trained by scripts/train_intent.py).
    3. Lightweight rule/regex-based entity extraction (dates, times,
       numbers, product/FAQ keywords) to complement the statistical model.
"""
 
import logging
import pickle
import re
import string
import numpy as np 
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
 
import config
 
logger = logging.getLogger(__name__)
 
for resource in ("punkt", "wordnet", "omw-1.4"):
    try:
        nltk.data.find(f"tokenizers/{resource}" if resource == "punkt" else f"corpora/{resource}")
    except LookupError:
        nltk.download(resource, quiet=True)
 
_lemmatizer = WordNetLemmatizer()
 
# Simple regex-based entity patterns; extend as the FAQ domain grows.
_ENTITY_PATTERNS = {
    "TIME": re.compile(r"\b\d{1,2}(:\d{2})?\s?(am|pm|AM|PM)?\b"),
    "DATE": re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|today|tomorrow|yesterday)\b", re.I),
    "NUMBER": re.compile(r"\b\d+\b"),
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
}
 
 
class NLUPipeline:
    """Cleans user text, predicts intent, and extracts entities."""
 
    def __init__(self, model_path: str = config.INTENT_MODEL_PATH):
        self.model_path = model_path
        self._classifier = None  # lazy-loaded (vectorizer + classifier pipeline)
 
    @property
    def classifier(self):
        if self._classifier is None:
            logger.info("Loading intent classifier from %s", self.model_path)
            with open(self.model_path, "rb") as f:
                self._classifier = pickle.load(f)
        return self._classifier
 
    # ------------------------------------------------------------------ #
    # Pre-processing
    # ------------------------------------------------------------------ #
    def preprocess(self, text: str) -> str:
        text = text.lower().strip()
        text = text.translate(str.maketrans("", "", string.punctuation))
        tokens = word_tokenize(text)
        lemmas = [_lemmatizer.lemmatize(tok) for tok in tokens]
        return " ".join(lemmas)
 
    # ------------------------------------------------------------------ #
    # Intent classification
    # ------------------------------------------------------------------ #
    def predict_intent(self, text: str):
        """Returns (intent_label: str, confidence: float)."""
        cleaned = self.preprocess(text)
 
        probabilities = np.array(self.classifier.predict_proba([cleaned])[0])
        classes = self.classifier.classes_
        if len(probabilities) == 0:
            return config.FALLBACK_INTENT, 0.0
        best_idx = probabilities.argmax()
        intent, confidence = classes[best_idx], float(probabilities[best_idx])
 
        if confidence < config.INTENT_CONFIDENCE_THRESHOLD:
            logger.debug("Confidence %.2f below threshold, using fallback intent.", confidence)
            return config.FALLBACK_INTENT, confidence
 
        logger.debug("Predicted intent=%s confidence=%.2f", intent, confidence)
        return intent, confidence
 
    # ------------------------------------------------------------------ #
    # Entity extraction
    # ------------------------------------------------------------------ #
    def extract_entities(self, text: str) -> dict:
        entities = {}
        for label, pattern in _ENTITY_PATTERNS.items():
            matches = [m.group().strip() for m in pattern.finditer(text) if m.group().strip()]
            if matches:
                entities[label] = matches
        return entities
 
    # ------------------------------------------------------------------ #
    # Convenience wrapper used by dialogue_manager
    # ------------------------------------------------------------------ #
    def analyze(self, text: str) -> dict:
        intent, confidence = self.predict_intent(text)
        entities = self.extract_entities(text)
        return {
            "raw_text": text,
            "cleaned_text": self.preprocess(text),
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
        }
 
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    nlu = NLUPipeline()
    print(nlu.analyze("What time does the library open tomorrow?"))
 

