"""Flask + Socket.IO entry point for the corrected chatbot."""
import logging
import os
import uuid

from flask import Config, Flask, jsonify, render_template, request, session
from flask_socketio import SocketIO, emit

import config
from config import Config
from modules.audio_converter import webm_to_pcm
from modules.asr import SpeechRecognizer
from modules.database import (
    db,
    dashboard_stats,
    get_or_create_conversation,
    log_intent,
    log_message,
    )
from modules.dialogue_manager import session_registry
from modules.nlu import NLUPipeline
from modules.response_generator import ResponseGenerator
from modules.tts import TextToSpeech
from modules.ai_engine import generate_ai_response
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from config import Config

load_dotenv()


client = genai.Client(api_key=Config.GEMINI_API_KEY)

response = client.models.generate_content(
    model = "gemini-3.6-flash",
    contents = 'Teach me about how an LLM works')

print(response.text)


logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.APP_LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=Config.SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=config.SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=config.SQLALCHEMY_TRACK_MODIFICATIONS,
    MAX_CONTENT_LENGTH=config.MAX_AUDIO_BYTES,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
)

db.init_app(app)

# Threading keeps the local project dependency-light. For a production
# deployment, use a Socket.IO-compatible server/configuration that is tested.
socketio = SocketIO(app, cors_allowed_origins="*")


speech_recognizer = SpeechRecognizer()
nlu_pipeline = NLUPipeline()
response_generator = ResponseGenerator()
text_to_speech = TextToSpeech()


def validate_text(value):
    if not isinstance(value, str):
        raise ValueError("Message must be text.")
    value = value.strip()
    if not value:
        raise ValueError("Empty message.")
    if len(value) > config.MAX_TEXT_LENGTH:
        raise ValueError(
            f"Message exceeds the {config.MAX_TEXT_LENGTH}-character limit."
        )
    return value


def get_session_id():
    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
    return session_id


def run_pipeline(session_id: str, user_text: str):
    conversation = get_or_create_conversation(session_id)
    log_message(conversation, sender="user", text=user_text)

    nlu_result = nlu_pipeline.analyze(user_text)
    log_intent(
        conversation,
        user_text,
        nlu_result["intent"],
        nlu_result["confidence"],
    )

    manager = session_registry.get_or_create(session_id)
    act = manager.step(nlu_result)
    bot_text = response_generator.generate(act, nlu_result, manager)

    audio_path = text_to_speech.synthesize(bot_text)
    audio_url = "/" + os.path.relpath(
        audio_path, config.BASE_DIR
    ).replace(os.sep, "/")

    log_message(
        conversation,
        sender="bot",
        text=bot_text,
        audio_path=audio_url,
    )
    manager.remember_bot_response(bot_text)

    return {
        "intent": nlu_result["intent"],
        "confidence": nlu_result["confidence"],
        "reply_text": bot_text,
        "reply_audio_url": audio_url,
    }


@app.route("/")
def index():
    get_session_id()
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    # The academic/local dashboard is protected when an admin token is configured.
    if config.ADMIN_TOKEN:
        supplied = request.headers.get("X-Admin-Token", "")
        if supplied != config.ADMIN_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
    return render_template("dashboard.html", stats=dashboard_stats())


@app.route("/api/chat/text", methods=["POST"])
def chat_text():
    payload = request.get_json(silent=True) or {}
    try:
        user_text = validate_text(payload.get("text", ""))
        result = run_pipeline(get_session_id(), user_text)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("Text pipeline failure")
        return jsonify({"error": "Internal server error."}), 500


@socketio.on("connect")
def handle_connect():
    logger.info("Client connected: %s", request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected: %s", request.sid)


@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    """Receive one complete WebM/Opus utterance and convert it to PCM."""
    try:
        data = data or {}
        session_id = data.get("session_id") or get_session_id()
        audio = data.get("audio")

        if isinstance(audio, memoryview):
            audio = audio.tobytes()
        elif isinstance(audio, bytearray):
            audio = bytes(audio)

        if not isinstance(audio, bytes) or not audio:
            emit("bot_error", {"error": "No audio received."})
            return

        if len(audio) > config.MAX_AUDIO_BYTES:
            emit("bot_error", {"error": "Audio payload is too large."})
            return

        pcm_audio = webm_to_pcm(audio)
        user_text = speech_recognizer.transcribe(pcm_audio)

        if not user_text:
            emit("bot_error", {"error": "Could not understand audio."})
            return

        emit("transcript", {"text": user_text})
        result = run_pipeline(session_id, user_text)
        emit("bot_reply", result)

    except Exception:
        logger.exception("Voice pipeline failure")
        emit("bot_error", {"error": "Voice processing failed."})

@socketio.on("message")
def handle_message(data):
    """Receive a message from the client and process it."""
    try:
        data = data or {}
        session_id = data.get("session_id") or get_session_id()
        user_text = validate_text(data.get("text", ""))

        result = run_pipeline(session_id, user_text)
        emit("bot_reply", result)

    except ValueError as exc:
        emit("bot_error", {"error": str(exc)})
    except Exception:
        logger.exception("Text pipeline failure")
        emit("bot_error", {"error": "Text processing failed."})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
