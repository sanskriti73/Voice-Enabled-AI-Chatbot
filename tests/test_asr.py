"""
tests/test_asr.py
Unit tests for modules/asr.py — verifies mode selection and fallback
behavior of the SpeechRecognizer without requiring real audio hardware
or network access (external calls are mocked).
"""
 
import wave
import io
from unittest.mock import patch, MagicMock
 
import pytest
 
from modules.asr import SpeechRecognizer
import config
 
 
def make_silent_wav_bytes(duration_sec=1, sample_rate=config.ASR_SAMPLE_RATE):
    n_samples = duration_sec * sample_rate
    return b"\x00\x00" * n_samples
 
 
def test_pcm_to_wav_produces_valid_wave_header():
    recognizer = SpeechRecognizer(mode="offline")
    pcm = make_silent_wav_bytes(duration_sec=1)
    wav_buffer = recognizer._pcm_to_wav(pcm)
 
    with wave.open(wav_buffer, "rb") as wf:
        assert wf.getframerate() == config.ASR_SAMPLE_RATE
        assert wf.getnchannels() == config.ASR_CHANNELS
        assert wf.getsampwidth() == 2
 
 
@patch("modules.asr.SpeechRecognizer._transcribe_online")
@patch("modules.asr.SpeechRecognizer._transcribe_offline")
def test_auto_mode_falls_back_to_offline_on_online_failure(mock_offline, mock_online):
    mock_online.side_effect = Exception("network unavailable")
    mock_offline.return_value = "hello world"
 
    recognizer = SpeechRecognizer(mode="auto")
    result = recognizer.transcribe(b"\x00\x00" * 1000)
 
    assert result == "hello world"
    mock_online.assert_called_once()
    mock_offline.assert_called_once()
 
 
@patch("modules.asr.SpeechRecognizer._transcribe_online")
def test_online_mode_does_not_call_offline(mock_online):
    mock_online.return_value = "test transcript"
    recognizer = SpeechRecognizer(mode="online")
 
    with patch.object(recognizer, "_transcribe_offline") as mock_offline:
        result = recognizer.transcribe(b"\x00\x00" * 1000)
        assert result == "test transcript"
        mock_offline.assert_not_called()
 
