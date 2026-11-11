"""Central configuration for the corrected Voice-Enabled AI Chatbot."""
from dotenv import load_dotenv
import os

load_dotenv()

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
class Config:

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    SECRET_KEY = os.environ.get("CHATBOT_SECRET_KEY", "")
    ADMIN_TOKEN = os.environ.get("CHATBOT_ADMIN_TOKEN", "")

    @staticmethod
    def validate():
        if not Config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set in .env file")
        if not Config.SECRET_KEY:
            raise RuntimeError("CHATBOT_SECRET_KEY is not set in .env file")
        if not Config.ADMIN_TOKEN:
            raise RuntimeError("CHATBOT_ADMIN_TOKEN is not set in .env file")
        

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Offline-first: browser audio is decoded to PCM before ASR.
ASR_MODE = os.environ.get("ASR_MODE", "offline").lower()
ASR_SAMPLE_RATE = 16000
ASR_CHANNELS = 1
VAD_AGGRESSIVENESS = 2
VAD_FRAME_MS = 30
SILENCE_TIMEOUT_SEC = 1.5

INTENT_CONFIDENCE_THRESHOLD = 0.55
FALLBACK_INTENT = "fallback"

KB_MATCH_THRESHOLD = 0.60
DIALOGPT_MODEL_NAME = "microsoft/DialoGPT-medium"
DIALOGPT_MAX_HISTORY_TURNS = 4
DIALOGPT_MAX_INPUT_TOKENS = 900

TTS_MODE = os.environ.get("TTS_MODE", "offline").lower()
TTS_VOICE_RATE = 175
TTS_VOICE_VOLUME = 1.0
TTS_LANGUAGE = "en"
TTS_CACHE_MAX_FILES = 200

MAX_TEXT_LENGTH = 500
MAX_AUDIO_BYTES = 10 * 1024 * 1024

ALLOWED_ORIGINS = [
    x.strip() for x in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5000"
    ).split(",") if x.strip()
]

ADMIN_TOKEN = os.environ.get("CHATBOT_ADMIN_TOKEN", "")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOGS_DIR, "errors.log")
