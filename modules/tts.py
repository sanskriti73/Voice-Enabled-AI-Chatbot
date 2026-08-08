"""
modules/tts.py
Dual-mode Text-to-Speech (TTS).
 
    * Offline -> pyttsx3 (on-device engine; works fully offline, voice
                 quality depends on the OS's installed voices).
    * Online  -> gTTS (Google Text-to-Speech; higher audio quality, but
                 requires an internet connection).
 
Generated audio is cached under static/audio/ so identical bot replies
don't need to be re-synthesized. A simple LRU-style cap keeps the cache
from growing without bound.
"""
 
import hashlib
import logging
import os
 
import pyttsx3
from gtts import gTTS
 
import config
 
logger = logging.getLogger(__name__)
 
 
class TextToSpeech:
    """Wraps both offline (pyttsx3) and online (gTTS) synthesis engines."""
 
    def __init__(self, mode: str = config.TTS_MODE):
        self.mode = mode
        self._offline_engine = None
 
    @property
    def offline_engine(self):
        if self._offline_engine is None:
            self._offline_engine = pyttsx3.init()
            self._offline_engine.setProperty("rate", config.TTS_VOICE_RATE)
            self._offline_engine.setProperty("volume", config.TTS_VOICE_VOLUME)
        return self._offline_engine
 
    def synthesize(self, text: str) -> str:
        """
        Convert text to speech and return the path of the cached WAV/MP3
        file (relative to static/), honoring TTS_MODE with fallback in
        "auto" mode, same pattern as the ASR module.
        """
        cache_path = self._cache_path_for(text)
        if os.path.exists(cache_path):
            logger.debug("TTS cache hit for text hash.")
            return cache_path
 
        if self.mode == "offline":
            self._synthesize_offline(text, cache_path)
        elif self.mode == "online":
            self._synthesize_online(text, cache_path)
        else:  # auto
            try:
                self._synthesize_online(text, cache_path)
            except Exception as exc:
                logger.warning("Online TTS failed (%s); falling back to offline pyttsx3.", exc)
                self._synthesize_offline(text, cache_path)
 
        self._enforce_cache_limit()
        return cache_path
 
    # ------------------------------------------------------------------ #
    def _synthesize_offline(self, text: str, out_path: str):
        engine = self.offline_engine
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        logger.debug("Synthesized offline (pyttsx3) audio -> %s", out_path)
 
    def _synthesize_online(self, text: str, out_path: str):
        tts = gTTS(text=text, lang=config.TTS_LANGUAGE)
        tts.save(out_path)
        logger.debug("Synthesized online (gTTS) audio -> %s", out_path)
 
    # ------------------------------------------------------------------ #
    @staticmethod
    def _cache_path_for(text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        filename = f"{digest}.mp3"
        return os.path.join(config.AUDIO_CACHE_DIR, filename)
 
    @staticmethod
    def _enforce_cache_limit():
        files = sorted(
            (os.path.join(config.AUDIO_CACHE_DIR, f) for f in os.listdir(config.AUDIO_CACHE_DIR)),
            key=os.path.getmtime,
        )
        excess = len(files) - config.TTS_CACHE_MAX_FILES
        for stale_file in files[:max(excess, 0)]:
            os.remove(stale_file)
            logger.debug("Evicted stale TTS cache file: %s", stale_file)
 
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tts = TextToSpeech(mode="offline")
    print(tts.synthesize("Hello, this is a test of the text to speech engine."))

