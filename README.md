# Voice-Enabled AI Chatbot System

## Overview

This project is a **Voice-Enabled AI Chatbot System** developed as an MCA final-year academic project.

The system combines speech recognition, natural language understanding, dialogue management, knowledge-base retrieval, response generation, and text-to-speech to provide conversational interaction through a web interface.

## Features

- Text-based chatbot interaction
- Browser-based voice input
- WebM/Opus audio conversion to PCM
- Offline speech recognition with Vosk
- Intent classification using TF-IDF and SVM
- Entity extraction
- Confidence-based intent fallback
- Finite-state dialogue management
- FAQ / knowledge-base retrieval
- Optional DialoGPT response generation
- Text-to-speech using pyttsx3 or gTTS
- SQLite database
- Conversation and intent logging
- Web dashboard
- Automated tests
- Windows one-click setup and run scripts

## Architecture

```text
User
 │
 ├── Text Input ──────────────┐
 │                            │
 └── Voice Input              │
        │                     │
        ▼                     │
   Audio Capture              │
        │                     │
        ▼                     │
   FFmpeg Conversion          │
        │                     │
        ▼                     │
   Vosk Speech Recognition    │
        │                     │
        └──────────┬──────────┘
                   ▼
                  NLU
             TF-IDF + SVM
                   │
                   ▼
          Dialogue Manager
                   │
                   ▼
         Response Generator
            │          │
            ▼          ▼
           FAQ      DialoGPT
            │          │
            └────┬─────┘
                 ▼
                 TTS
                 │
                 ▼
           Audio Response
```

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Backend | Flask |
| Real-time communication | Flask-SocketIO |
| Frontend | HTML, CSS, JavaScript |
| Speech Recognition | Vosk |
| Audio Conversion | FFmpeg |
| NLU | TF-IDF + SVM |
| NLP | NLTK |
| Response Retrieval | TF-IDF / Cosine Similarity |
| Neural Response | DialoGPT |
| Text-to-Speech | pyttsx3 / gTTS |
| Database | SQLite / Flask-SQLAlchemy |
| Testing | pytest |
| Deployment | Gunicorn / Flask-SocketIO |

## Project Structure

```text
Voice-Enabled-AI-Chatbot/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── Dockerfile
├── setup.bat
├── run.bat
│
├── modules/
│   ├── audio_capture.py
│   ├── audio_converter.py
│   ├── asr.py
│   ├── nlu.py
│   ├── dialogue_manager.py
│   ├── response_generator.py
│   ├── tts.py
│   └── database.py
│
├── datasets/
│   ├── intents.json
│   └── faq_seed.csv
│
├── models/
│   ├── README.txt
│   ├── vosk-model-en-us-0.22/
│   └── intent_classifier.pkl
│
├── scripts/
│   ├── init_db.py
│   ├── seed_kb.py
│   └── train_intent.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── audio/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   └── dashboard.html
│
└── tests/
    ├── test_asr.py
    ├── test_audio_converter.py
    ├── test_nlu.py
    ├── test_dialogue.py
    └── test_integration.py
```

## Requirements

- Windows 10/11
- Python 3.10+
- FFmpeg
- Compatible Vosk model
- Internet connection for installing Python packages

## Quick Start — Windows

### 1. Extract the project

Extract the ZIP to a folder of your choice.

### 2. Run setup

Double-click:

```text
setup.bat
```

The setup script creates the virtual environment, installs dependencies, prepares project directories, initializes the database, and trains the intent classifier.

### 3. Install the Vosk model

Place the extracted Vosk model at:

```text
models/vosk-model-en-us-0.22/
```

The large Vosk model is not bundled with the source ZIP.

### 4. Start the application

Double-click:

```text
run.bat
```

Then open:

```text
http://localhost:5000
```

## Manual Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize the database:

```bash
python scripts/init_db.py
```

Seed/validate the knowledge base:

```bash
python scripts/seed_kb.py
```

Train the intent classifier:

```bash
python scripts/train_intent.py
```

Run the application:

```bash
python app.py
```

## Environment Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

Configure secrets and application settings there. Do not commit real credentials or production secrets to Git.

## Voice Pipeline

The browser records compressed audio. Before speech recognition, the audio is converted to the format expected by Vosk:

```text
Browser MediaRecorder
        ↓
WebM / Opus
        ↓
FFmpeg
        ↓
16 kHz / Mono / 16-bit PCM
        ↓
Vosk
        ↓
Recognized Text
```

FFmpeg must therefore be installed and available in the Windows PATH.

## NLU Pipeline

```text
User Text
   ↓
Preprocessing
   ↓
TF-IDF Features
   ↓
SVM Classifier
   ↓
Intent + Confidence
   ↓
Entity Extraction
```

Low-confidence predictions can be handled through the configured fallback behavior.

## Response Generation

The response layer can retrieve an answer from the FAQ/knowledge base using similarity matching. When an appropriate FAQ answer is not found, the configured fallback response generator can be used.

```text
User Query
    ↓
Knowledge Base Search
    ↓
Similarity Threshold
   ↙              ↘
Match            No Match
 ↓                  ↓
FAQ Answer       Fallback
```

## Text-to-Speech

Supported modes include:

- `pyttsx3` for local/offline speech synthesis
- `gTTS` for online speech synthesis

The output format should match the selected engine.

## Database

The application uses SQLite with Flask-SQLAlchemy for persistent application data.

The database can contain information such as:

- Conversations
- Messages
- Intent logs
- Timestamps
- Confidence values

Generated database files should not be committed to the repository.

## Testing

Run the test suite:

```bash
pytest -q
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

## Troubleshooting

### Python is not recognized

Check:

```cmd
python --version
```

or:

```cmd
py --version
```

Install Python and enable the option to add Python to PATH if necessary.

### FFmpeg is not recognized

Check:

```cmd
ffmpeg -version
```

Install FFmpeg and add its `bin` directory to PATH.

### Vosk model not found

Verify:

```text
models/vosk-model-en-us-0.22/
```

exists and contains the extracted model files.

### Intent classifier missing

Run:

```bash
python scripts/train_intent.py
```

### Port 5000 is already in use

Stop the application using the port or configure another port before starting the server.

### Microphone does not work

Check:

1. Browser microphone permission.
2. Windows microphone privacy settings.
3. Correct microphone selection.
4. FFmpeg installation.
5. Browser developer-console errors.

## Security

The project should be configured with:

- Strong application secret keys
- Debug mode disabled for production
- Restricted allowed origins
- Secure session configuration when HTTPS is used
- Input length limits
- Audio upload limits
- Protected dashboard access

Never commit `.env` or other files containing secrets.

## Docker

Build the image:

```bash
docker build -t voice-chatbot .
```

Run:

```bash
docker run --rm -p 5000:5000 voice-chatbot
```

The Vosk model must be supplied separately when it is not included in the image.

## Project Objective

The primary objective is to design and develop a conversational AI system capable of:

1. Accepting text and spoken input.
2. Converting speech into text.
3. Identifying user intent.
4. Extracting relevant entities.
5. Maintaining conversational state.
6. Retrieving relevant knowledge-base information.
7. Generating an appropriate response.
8. Converting the response into speech.
9. Recording useful conversation and intent information.

## Limitations

Actual speech-recognition accuracy, response quality, and latency depend on the hardware, microphone, acoustic environment, selected models, configuration, and workload.

Any numerical performance claims should be considered valid only when reproduced through a documented benchmark on the target environment.

## Future Enhancements

Potential improvements include:

- Hindi and multilingual speech recognition
- Noise suppression
- Wake-word detection
- Improved transformer-based NLU
- Retrieval-Augmented Generation (RAG)
- Larger domain-specific knowledge bases
- User authentication
- Persistent user profiles
- Advanced analytics
- Cloud deployment
- HTTPS
- CI/CD integration
- Improved accessibility and mobile support

## Academic Information

**Project Title:** Design and Development of a Voice-Enabled Artificial Intelligence Chatbot System

**Project Type:** MCA Final-Year Academic Project

## License

This project is intended primarily for academic and educational use. Add a separate `LICENSE` file if a specific open-source or distribution license is required.

## Author

**MCA Final-Year Project**

**Voice-Enabled Artificial Intelligence Chatbot System**
