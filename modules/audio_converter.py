"""Convert browser WebM/Opus audio to the PCM format expected by Vosk."""
import shutil
import subprocess


def webm_to_pcm(webm_bytes: bytes) -> bytes:
    if not webm_bytes:
        raise ValueError("Empty WebM payload.")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg is required for browser voice input but was not found."
        )

    process = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            "pipe:1",
        ],
        input=webm_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Invalid/unsupported audio: {detail}")

    if not process.stdout:
        raise ValueError("FFmpeg produced no PCM audio.")

    return process.stdout
