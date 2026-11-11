from unittest.mock import patch, MagicMock
import pytest

from modules.audio_converter import webm_to_pcm


def test_empty_webm_is_rejected():
    with pytest.raises(ValueError):
        webm_to_pcm(b"")


@patch("modules.audio_converter.shutil.which", return_value=None)
def test_ffmpeg_is_required(mock_which):
    with pytest.raises(RuntimeError):
        webm_to_pcm(b"not-real-webm")


@patch("modules.audio_converter.shutil.which", return_value="/usr/bin/ffmpeg")
@patch("modules.audio_converter.subprocess.run")
def test_ffmpeg_output_is_returned(mock_run, mock_which):
    result = MagicMock()
    result.returncode = 0
    result.stdout = b"\x00\x00\x00\x00"
    result.stderr = b""
    mock_run.return_value = result

    assert webm_to_pcm(b"webm") == result.stdout
