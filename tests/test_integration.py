"""
tests/test_integration.py
End-to-end integration test exercising the full text-chat pipeline via
the Flask test client: HTTP request -> NLU -> dialogue manager ->
response generator -> TTS -> JSON response, with the heavy external
dependencies (intent classifier, TTS engines, DialoGPT) mocked out so
the test suite runs quickly and offline in CI.
"""
 
from unittest.mock import patch, MagicMock
 
import pytest
 
import app as app_module
 
 
@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    app_module.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app_module.app.app_context():
        app_module.db.create_all()
    with app_module.app.test_client() as client:
        yield client
 
 
@patch("app.text_to_speech.synthesize", return_value="static/audio/mock.mp3")
@patch("app.response_generator.generate", return_value="Hello! How can I help you today?")
@patch("app.nlu_pipeline.analyze", return_value={
    "raw_text": "hi",
    "cleaned_text": "hi",
    "intent": "greeting",
    "confidence": 0.95,
    "entities": {},
})
def test_text_chat_endpoint_returns_bot_reply(mock_analyze, mock_generate, mock_tts, client):
    response = client.post("/api/chat/text", json={"text": "hi"})
    assert response.status_code == 200
 
    data = response.get_json()
    assert data["intent"] == "greeting"
    assert data["reply_text"] == "Hello! How can I help you today?"
    assert "reply_audio_url" in data
 
 
def test_text_chat_endpoint_rejects_empty_message(client):
    response = client.post("/api/chat/text", json={"text": "   "})
    assert response.status_code == 400
 
 
def test_dashboard_route_renders(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
