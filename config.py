"""
config.py
Central configuration for the Voice-Enabled AI Chatbot System.
All paths, API keys, and tunable thresholds are defined here so that no
other module needs to hard-code a literal value.
"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if present
import os
class Config:
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
 
# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
STATIC_DIR = os.path.join(BASE_DIR, "static")
AUDIO_CACHE_DIR = os.path.join(STATIC_DIR, "audio")
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
 
VOSK_MODEL_PATH = os.path.join(MODELS_DIR, "vosk-model-en-us-0.22")
INTENT_MODEL_PATH = os.path.join(MODELS_DIR, "intent_classifier.pkl")
INTENTS_JSON_PATH = os.path.join(DATASETS_DIR, "intents.json")
FAQ_CSV_PATH = os.path.join(DATASETS_DIR, "faq_seed.csv")
 
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
 
# ---------------------------------------------------------------------------
# Flask / SQLAlchemy
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "ad75261d8f65e3016ebbca117e124adf952c332aa254017e18907495ae0475cf")
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "database.db"))
SQLALCHEMY_TRACK_MODIFICATIONS = False
 
# ---------------------------------------------------------------------------
# ASR (Automatic Speech Recognition) settings
# ---------------------------------------------------------------------------
# "offline"  -> Vosk (runs fully on-device, no internet required)
# "online"   -> Google Cloud Speech-to-Text (via SpeechRecognition library)
# "auto"     -> try online first, fall back to offline if no connectivity
ASR_MODE = os.environ.get("ASR_MODE", "auto")
ASR_SAMPLE_RATE = 16000
ASR_CHANNELS = 1
 
# Voice Activity Detection (VAD) aggressiveness: 0 (least) - 3 (most aggressive)
VAD_AGGRESSIVENESS = 2
VAD_FRAME_MS = 30
SILENCE_TIMEOUT_SEC = 1.5
 
# ---------------------------------------------------------------------------
# NLU settings
# ---------------------------------------------------------------------------
INTENT_CONFIDENCE_THRESHOLD = 0.55
FALLBACK_INTENT = "fallback"
 
# ---------------------------------------------------------------------------
# Response generation
# ---------------------------------------------------------------------------
# If the KB / FAQ lookup confidence is below this, the hybrid generator
# falls back to the DialoGPT neural model for an open-domain response.
KB_MATCH_THRESHOLD = 0.60
DIALOGPT_MODEL_NAME = "microsoft/DialoGPT-medium"
DIALOGPT_MAX_HISTORY_TURNS = 4


class Config:
    # ... existing settings
    OLLAMA_MODEL = "llama3.2"
    USE_OLLAMA = True  # switch between local Ollama
# ---------------------------------------------------------------------------
# TTS (Text-to-Speech) settings
# ---------------------------------------------------------------------------
# "offline" -> pyttsx3 (on-device engine, no internet needed)
# "online"  -> gTTS (Google Text-to-Speech, requires internet)
# "auto"    -> try online first, fall back to offline
TTS_MODE = os.environ.get("TTS_MODE", "auto")
TTS_VOICE_RATE = 175
TTS_VOICE_VOLUME = 1.0
TTS_LANGUAGE = "en"
TTS_CACHE_MAX_FILES = 200
 


 
# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOGS_DIR, "errors.log")



