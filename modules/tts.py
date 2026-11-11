"""Offline pyttsx3 / online gTTS synthesis with format-correct caching."""
import hashlib
import logging
import os
import time

import config

logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(self, mode=config.TTS_MODE):
        if mode not in {"offline", "online", "auto"}:
            raise ValueError("TTS_MODE must be offline, online, or auto.")
        self.mode = mode
        self._offline_engine = None

    @property
    def offline_engine(self):
        if self._offline_engine is None:
            import pyttsx3
            self._offline_engine = pyttsx3.init()
            self._offline_engine.setProperty(
                "rate", config.TTS_VOICE_RATE
            )
            self._offline_engine.setProperty(
                "volume", config.TTS_VOICE_VOLUME
            )
        return self._offline_engine

    def synthesize(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            raise ValueError("Cannot synthesize empty text.")

        mode = self.mode
        if mode == "auto":
            mode = "online"

        extension = "wav" if mode == "offline" else "mp3"
        cache_path = self._cache_path_for(text, extension)

        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            os.utime(cache_path, None)
            return cache_path

        try:
            if mode == "offline":
                self._synthesize_offline(text, cache_path)
            else:
                self._synthesize_online(text, cache_path)
        except Exception:
            if self.mode == "auto":
                logger.warning("Online TTS failed; using offline TTS.", exc_info=True)
                cache_path = self._cache_path_for(text, "wav")
                self._synthesize_offline(text, cache_path)
            else:
                raise

        self._enforce_cache_limit()
        return cache_path

    def _synthesize_offline(self, text, out_path):
        engine = self.offline_engine
        engine.save_to_file(text, out_path)
        engine.runAndWait()

    @staticmethod
    def _synthesize_online(text, out_path):
        from gtts import gTTS
        gTTS(text=text, lang=config.TTS_LANGUAGE).save(out_path)

    @staticmethod
    def _cache_path_for(text, extension):
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return os.path.join(
            config.AUDIO_CACHE_DIR,
            f"{digest}.{extension}",
        )

    @staticmethod
    def _enforce_cache_limit():
        files = [
            os.path.join(config.AUDIO_CACHE_DIR, name)
            for name in os.listdir(config.AUDIO_CACHE_DIR)
            if name.lower().endswith((".wav", ".mp3"))
        ]
        files.sort(key=os.path.getmtime)
        excess = len(files) - config.TTS_CACHE_MAX_FILES
        for path in files[:max(excess, 0)]:
            try:
                os.remove(path)
            except OSError:
                logger.warning("Could not remove cache file %s", path)
