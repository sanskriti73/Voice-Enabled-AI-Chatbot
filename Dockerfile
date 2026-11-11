FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build-time validation; the Vosk model is supplied separately because it is
# large and intentionally excluded from Git.
RUN python scripts/seed_kb.py
RUN python scripts/train_intent.py

EXPOSE 5000
ENV ASR_MODE=offline
ENV TTS_MODE=offline

CMD ["python", "app.py"]
