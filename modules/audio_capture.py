"""Optional desktop microphone capture using PyAudio + WebRTC VAD."""
import collections
import logging
import time

import pyaudio
import webrtcvad

import config

logger = logging.getLogger(__name__)


class AudioCapture:
    """Capture raw 16-bit PCM mono audio and segment it using WebRTC VAD."""

    def __init__(
        self,
        sample_rate=config.ASR_SAMPLE_RATE,
        frame_ms=config.VAD_FRAME_MS,
        aggressiveness=config.VAD_AGGRESSIVENESS,
        silence_timeout=config.SILENCE_TIMEOUT_SEC,
    ):
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_bytes = int(sample_rate * frame_ms / 1000 * 2)
        self.silence_timeout = silence_timeout
        self.vad = webrtcvad.Vad(aggressiveness)
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None

    def open_stream(self):
        if self.stream is not None:
            return
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=config.ASR_CHANNELS,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=int(self.sample_rate * self.frame_ms / 1000),
        )

    def close_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.pyaudio_instance.terminate()

    def _read_frame(self):
        if self.stream is None:
            raise RuntimeError("Microphone stream is not open.")
        return self.stream.read(
            int(self.sample_rate * self.frame_ms / 1000),
            exception_on_overflow=False,
        )

    def listen_for_utterance(self) -> bytes:
        if self.stream is None:
            self.open_stream()

        ring_buffer = collections.deque(maxlen=10)
        triggered = False
        voiced_frames = []
        last_voice_time = time.monotonic()

        while True:
            frame = self._read_frame()
            is_speech = self.vad.is_speech(frame, self.sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = sum(1 for _, speech in ring_buffer if speech)
                if num_voiced > 0.6 * ring_buffer.maxlen:
                    triggered = True
                    voiced_frames.extend(frame for frame, _ in ring_buffer)
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                if is_speech:
                    last_voice_time = time.monotonic()
                elif time.monotonic() - last_voice_time > self.silence_timeout:
                    break

        return b"".join(voiced_frames)
