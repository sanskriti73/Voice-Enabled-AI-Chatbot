import io
import wave
from unittest.mock import patch

from modules.asr import SpeechRecognizer
import config


def pcm_silence(seconds=1):
    return b"\x00\x00" * int(seconds * config.ASR_SAMPLE_RATE)


def test_pcm_to_wav_produces_valid_header():
    recognizer = SpeechRecognizer(mode="offline")
    buffer = recognizer._pcm_to_wav(pcm_silence())

    with wave.open(buffer, "rb") as wav_file:
        assert wav_file.getframerate() == 16000
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2


@patch("modules.asr.SpeechRecognizer._transcribe_online")
@patch("modules.asr.SpeechRecognizer._transcribe_offline")
def test_auto_falls_back_to_offline(mock_offline, mock_online):
    mock_online.side_effect = RuntimeError("network unavailable")
    mock_offline.return_value = "hello world"

    recognizer = SpeechRecognizer(mode="auto")
    assert recognizer.transcribe(pcm_silence()) == "hello world"
    mock_online.assert_called_once()
    mock_offline.assert_called_once()
