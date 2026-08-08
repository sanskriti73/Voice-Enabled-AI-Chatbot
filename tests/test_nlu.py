"""
tests/test_nlu.py
Unit tests for modules/nlu.py — pre-processing, entity extraction, and
intent-confidence thresholding logic.
"""
 
from unittest.mock import MagicMock, patch
 
import pytest
 
from modules.nlu import NLUPipeline
import config
 
 
def test_preprocess_lowercases_and_strips_punctuation():
    nlu = NLUPipeline()
    cleaned = nlu.preprocess("Hello, World!!")
    assert "hello" in cleaned
    assert "," not in cleaned
    assert "!" not in cleaned
 
 
def test_extract_entities_finds_email_and_number():
    nlu = NLUPipeline()
    entities = nlu.extract_entities("Contact me at test@example.com or call 12345")
    assert "EMAIL" in entities
    assert "test@example.com" in entities["EMAIL"]
    assert "NUMBER" in entities
 
 
@patch.object(NLUPipeline, "classifier", new_callable=MagicMock)
def test_predict_intent_returns_fallback_below_threshold(mock_classifier):
    nlu = NLUPipeline()
 
    mock_model = MagicMock()
    mock_model.classes_ = ["greeting", "goodbye"]
    mock_model.predict_proba.return_value = [[0.4, 0.3]]
    nlu._classifier = mock_model
 
    intent, confidence = nlu.predict_intent("some ambiguous text")
    assert intent == config.FALLBACK_INTENT
    assert confidence < config.INTENT_CONFIDENCE_THRESHOLD
 
 
def test_analyze_returns_expected_keys():
    nlu = NLUPipeline()
    mock_model = MagicMock()
    mock_model.classes_ = ["greeting"]
    mock_model.predict_proba.return_value = [[0.9]]
    nlu._classifier = mock_model
 
    result = nlu.analyze("hello there")
    assert set(result.keys()) == {"raw_text", "cleaned_text", "intent", "confidence", "entities"}
 


