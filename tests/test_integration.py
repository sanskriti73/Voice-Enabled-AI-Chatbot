from unittest.mock import patch

import pytest

import app as app_module


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True

    # SQLAlchemy was initialized when app.py imported; therefore the original
    # URI must not be changed here. Isolate the schema within the test.
    with app_module.app.app_context():
        app_module.db.drop_all()
        app_module.db.create_all()

    with app_module.app.test_client() as test_client:
        yield test_client

    with app_module.app.app_context():
        app_module.db.drop_all()


@patch("app.text_to_speech.synthesize", return_value="static/audio/mock.wav")
@patch("app.response_generator.generate", return_value="Hello!")
@patch(
    "app.nlu_pipeline.analyze",
    return_value={
        "raw_text": "hi",
        "cleaned_text": "hi",
        "intent": "greeting",
        "confidence": 0.95,
        "entities": {},
    },
)
def test_text_endpoint(mock_nlu, mock_generate, mock_tts, client):
    response = client.post("/api/chat/text", json={"text": "hi"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["intent"] == "greeting"
    assert data["reply_text"] == "Hello!"
    assert data["reply_audio_url"].endswith(".wav")


def test_empty_message_rejected(client):
    response = client.post("/api/chat/text", json={"text": " "})
    assert response.status_code == 400
