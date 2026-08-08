# Voice-Enabled AI Chatbot System
 
MCSP-232 IGNOU MCA Capstone Project.
 
A Flask-based web application that lets a user talk (or type) to an AI
chatbot. Speech is transcribed with a dual-mode ASR engine (offline
Vosk / online Google Cloud STT), understood with a TF-IDF + SVM intent
classifier, routed through a finite-state-machine dialogue manager, and
answered by a hybrid response generator that prefers a curated FAQ
knowledge base and falls back to a DialoGPT neural model for
open-domain replies. Replies are spoken back using a dual-mode TTS
engine (offline pyttsx3 / online gTTS).
 
## Project layout
 
See the module docstrings in `modules/` for details on each pipeline
stage, and `app.py` for how they are wired together.
 
## Setup
 
```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
 
python scripts/init_db.py       # create database.db
python scripts/train_intent.py  # train models/intent_classifier.pkl
python scripts/seed_kb.py       # load datasets/faq_seed.csv into the DB
 
python app.py                   # runs on http://localhost:5000
```
 
## Running tests
 
```bash
pytest tests/
```
