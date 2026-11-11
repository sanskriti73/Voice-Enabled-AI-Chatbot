from unittest.mock import MagicMock
import numpy as np
from modules.nlu import NLUPipeline
import config


def test_preprocess():
    nlu = NLUPipeline()
    cleaned = nlu.preprocess("Hello, World!!")
    assert "hello" in cleaned
    assert "," not in cleaned
    assert "!" not in cleaned


def test_extract_entities():
    nlu = NLUPipeline()
    entities = nlu.extract_entities(
        "Contact test@example.com at 12345 at 10:30 am."
    )
    assert "EMAIL" in entities
    assert "NUMBER" in entities
    assert "TIME" in entities


def test_low_confidence_becomes_fallback():
    nlu = NLUPipeline()
    model = MagicMock()
    model.classes_ = ["greeting", "goodbye"]
    model.predict_proba.return_value =np.array([[0.40, 0.30]])
    nlu._classifier = model

    intent, confidence = nlu.predict_intent("ambiguous")
    assert intent == config.FALLBACK_INTENT
    assert confidence < config.INTENT_CONFIDENCE_THRESHOLD


def test_empty_input_is_fallback():
    nlu = NLUPipeline()
    intent, confidence = nlu.predict_intent("")
    assert intent == config.FALLBACK_INTENT
    assert confidence == 0.0
