"""Offline-first ASR using Vosk, with optional Google fallback."""
import io
import json
import logging
import wave

import speech_recognition as sr
from vosk import KaldiRecognizer, Model

import config

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    def __init__(self, mode=config.ASR_MODE):
        if mode not in {"offline", "online", "auto"}:
            raise ValueError("ASR_MODE must be offline, online, or auto.")
        self.mode = mode
        self._vosk_model = None
        self._recognizer = sr.Recognizer()

    @property
    def vosk_model(self):
        if self._vosk_model is None:
            if not __import__("os").path.isdir(config.VOSK_MODEL_PATH):
                raise FileNotFoundError(
                    f"Vosk model not found: {config.VOSK_MODEL_PATH}"
                )
            logger.info("Loading Vosk model from %s", config.VOSK_MODEL_PATH)
            self._vosk_model = Model(config.VOSK_MODEL_PATH)
        return self._vosk_model

    def transcribe(self, pcm_audio: bytes) -> str:
        if not pcm_audio:
            return ""

        if self.mode == "offline":
            return self._transcribe_offline(pcm_audio)
        if self.mode == "online":
            return self._transcribe_online(pcm_audio)

        try:
            online = self._transcribe_online(pcm_audio)
            if online:
                return online
        except Exception as exc:
            logger.warning("Online ASR failed: %s", exc)

        return self._transcribe_offline(pcm_audio)

    def _transcribe_offline(self, pcm_audio: bytes) -> str:
        recognizer = KaldiRecognizer(
            self.vosk_model,
            config.ASR_SAMPLE_RATE,
        )
        recognizer.SetWords(True)

        for start in range(0, len(pcm_audio), 4000):
            recognizer.AcceptWaveform(pcm_audio[start:start + 4000])

        result = json.loads(recognizer.FinalResult())
        return result.get("text", "").strip()

    def _transcribe_online(self, pcm_audio: bytes) -> str:
        wav_buffer = self._pcm_to_wav(pcm_audio)
        with sr.AudioFile(wav_buffer) as source:
            audio_data = self._recognizer.record(source)
        return self._recognizer.recognize_google(audio_data).strip()

    @staticmethod
    def _pcm_to_wav(pcm_audio: bytes) -> io.BytesIO:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(config.ASR_CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(config.ASR_SAMPLE_RATE)
            wf.writeframes(pcm_audio)
        buffer.seek(0)
        return buffer
