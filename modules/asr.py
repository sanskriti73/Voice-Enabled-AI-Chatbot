"""
modules/asr.py
Dual-mode Automatic Speech Recognition (ASR).
 
Two engines are supported:
    * Offline -> Vosk (fully on-device, works without internet)
    * Online  -> Google Cloud Speech-to-Text (via the `speech_recognition`
                 library), more accurate but requires connectivity.
 
`ASR_MODE` in config.py controls which engine(s) are used:
    "offline" -> Vosk only
    "online"  -> Google Cloud STT only
    "auto"    -> try online first, transparently fall back to offline
                 if the network call fails or times out.
"""
 
import json
import logging
import wave
import io
 
import speech_recognition as sr
from vosk import Model, KaldiRecognizer
 
import config
 
logger = logging.getLogger(__name__)

class SpeechRecognizer:
    """Wraps both offline (Vosk) and online (Google Cloud) ASR engines."""
 
    def __init__(self, mode: str = config.ASR_MODE):
        self.mode = mode
        self._vosk_model = None
        self._recognizer = sr.Recognizer()
 
    # ------------------------------------------------------------------ #
    # Lazy-loaded offline model (Vosk model files are large, only load
    # them the first time offline recognition is actually needed).
    # ------------------------------------------------------------------ #
    @property
    def vosk_model(self) -> Model:
        if self._vosk_model is None:
            logger.info("Loading Vosk offline model from %s", config.VOSK_MODEL_PATH)
            self._vosk_model = Model(config.VOSK_MODEL_PATH)
        return self._vosk_model
 
    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def transcribe(self, pcm_audio: bytes) -> str:
        """
        Transcribe raw 16-bit PCM mono audio bytes to text, honoring the
        configured ASR_MODE with automatic fallback in "auto" mode.
        """
        if self.mode == "offline":
            return self._transcribe_offline(pcm_audio)
        if self.mode == "online":
            return self._transcribe_online(pcm_audio)
 
        # auto mode: try online, gracefully fall back to offline
        try:
            text = self._transcribe_online(pcm_audio)
            if text:
                return text
            logger.warning("Online ASR returned empty result, falling back to offline.")
        except Exception as exc:  # network error, quota error, etc.
            logger.warning("Online ASR failed (%s); falling back to offline Vosk.", exc)
 
        return self._transcribe_offline(pcm_audio)
 
    # ------------------------------------------------------------------ #
    # Offline engine (Vosk)
    # ------------------------------------------------------------------ #
    def _transcribe_offline(self, pcm_audio: bytes) -> str:
        recognizer = KaldiRecognizer(self.vosk_model, config.ASR_SAMPLE_RATE)
        recognizer.SetWords(True)
 
        chunk_size = 4000
        for i in range(0, len(pcm_audio), chunk_size):
            recognizer.AcceptWaveform(pcm_audio[i:i + chunk_size])
 
        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "").strip()
        logger.debug("Vosk (offline) transcription: %r", text)
        return text
 
    # ------------------------------------------------------------------ #
    # Online engine (Google Cloud Speech-to-Text)
    # ------------------------------------------------------------------ #
    def _transcribe_online(self, pcm_audio: bytes) -> str:
        wav_buffer = self._pcm_to_wav(pcm_audio)
        with sr.AudioFile(wav_buffer) as source:
            audio_data = self._recognizer.record(source)
 
        text = self._recognizer.recognize_google(audio_data)
        logger.debug("Google Cloud (online) transcription: %r", text)
        return text.strip()
 
    @staticmethod
    def _pcm_to_wav(pcm_audio: bytes) -> io.BytesIO:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(config.ASR_CHANNELS)
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(config.ASR_SAMPLE_RATE)
            wf.writeframes(pcm_audio)
        buffer.seek(0)
        return buffer
 
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    recognizer = SpeechRecognizer(mode="offline")
    with open("sample.raw", "rb") as f:
        print(recognizer.transcribe(f.read()))

