from VoiceenabledAIChatbot.ai import get_response
from VoiceenabledAIChatbot.tts import speak
"""
app.py
Flask application entry point for the Voice-Enabled AI Chatbot System.
 
Wires together the full pipeline:
    audio_capture -> asr -> nlu -> dialogue_manager -> response_generator -> tts
 
Exposes:
    GET  /                 -> main chat UI (templates/index.html)
    GET  /dashboard        -> admin analytics page (templates/dashboard.html)
    POST /api/chat/text    -> text-only chat turn (JSON in/out)
    Socket.IO "audio_chunk"-> streamed voice turns from recorder.js
"""
 
import logging
import os
import uuid
 
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
 
import config
from modules.database import (
    db, get_or_create_conversation, log_message, log_intent, dashboard_stats,
)
from modules.asr import SpeechRecognizer
from modules.nlu import NLUPipeline
from modules.dialogue_manager import session_registry
from modules.response_generator import ResponseGenerator
from modules.tts import TextToSpeech
 
# --------------------------------------------------------------------- #
# App / extension setup
# --------------------------------------------------------------------- #
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
 
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
 
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.APP_LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
 
# Pipeline components (loaded once, reused across requests)
speech_recognizer = SpeechRecognizer()
nlu_pipeline = NLUPipeline()
response_generator = ResponseGenerator()
text_to_speech = TextToSpeech()
 
 
# --------------------------------------------------------------------- #
# Core pipeline function shared by both text and voice entry points
# --------------------------------------------------------------------- #
def run_pipeline(session_id: str, user_text: str):
    conversation = get_or_create_conversation(session_id)
    log_message(conversation, sender="user", text=user_text)
 
    nlu_result = nlu_pipeline.analyze(user_text)
    log_intent(conversation, user_text, nlu_result["intent"], nlu_result["confidence"])
 
    dialogue_manager = session_registry.get_or_create(session_id)
    act = dialogue_manager.step(nlu_result)
 
    bot_text = response_generator.generate(act, nlu_result, dialogue_manager)
    audio_path = text_to_speech.synthesize(bot_text)
    audio_url = "/" + os.path.relpath(audio_path, config.BASE_DIR).replace(os.sep, "/")
 
    log_message(conversation, sender="bot", text=bot_text, audio_path=audio_url)
 
    return {
        "intent": nlu_result["intent"],
        "confidence": nlu_result["confidence"],
        "reply_text": bot_text,
        "reply_audio_url": audio_url,
    }
 
 
# --------------------------------------------------------------------- #
# HTTP routes
# --------------------------------------------------------------------- #
@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")
 
 
@app.route("/dashboard")
def dashboard():
    stats = dashboard_stats()
    return render_template("dashboard.html", stats=stats)
 
 
@app.route("/api/chat/text", methods=["POST"])
def chat_text():
    payload = request.get_json(force=True)
    user_text = (payload or {}).get("text", "").strip()
    session_id = session.get("session_id") or str(uuid.uuid4())
    session["session_id"] = session_id
 
    if not user_text:
        return jsonify({"error": "Empty message."}), 400
 
    result = run_pipeline(session_id, user_text)
    return jsonify(result)
 
 
# --------------------------------------------------------------------- #
# Socket.IO events (used for streamed voice turns from recorder.js)
# --------------------------------------------------------------------- #
@socketio.on("connect")
def handle_connect():
    logger.info("Client connected: %s", request.sid)
 
 
@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected: %s", request.sid)
 
 
@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    """
    `data` is expected to be a dict: {"session_id": str, "audio": bytes}
    containing one complete utterance's raw PCM audio (segmented
    client-side using recorder.js's VAD-driven stop logic).
    """
    session_id = data.get("session_id") or request.sid
    pcm_audio = data.get("audio")
 
    if not pcm_audio:
        emit("bot_error", {"error": "No audio received."})
        return
 
    user_text = speech_recognizer.transcribe(pcm_audio)
    if not user_text:
        emit("bot_error", {"error": "Could not understand audio."})
        return
 
    emit("transcript", {"text": user_text})
    result = run_pipeline(session_id, user_text)
    emit("bot_reply", result)
 
 
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

