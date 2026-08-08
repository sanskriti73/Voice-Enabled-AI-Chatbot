"""
modules/database.py
SQLAlchemy ORM models and query helpers for persisting conversations,
messages, users, and intent-recognition logs.
 
Tables:
    User          - one row per chat visitor (anonymous or named)
    Conversation  - one row per chat session
    Message       - one row per user/bot turn within a conversation
    IntentLog     - one row per NLU prediction, used for analytics on
                    the dashboard (accuracy over time, common intents)
    FAQEntry      - mirrors datasets/faq_seed.csv so the KB can be
                    edited/extended from the admin dashboard as well
"""
 
import datetime
import logging
 
from flask_sqlalchemy import SQLAlchemy
 
logger = logging.getLogger(__name__)
 
db = SQLAlchemy()
 
 
class User(db.Model):
    __tablename__ = "users"
 
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
 
    conversations = db.relationship("Conversation", backref="user", lazy=True)
 
 
class Conversation(db.Model):
    __tablename__ = "conversations"
 
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
 
    messages = db.relationship("Message", backref="conversation", lazy=True,
                                cascade="all, delete-orphan")
 
 
class Message(db.Model):
    __tablename__ = "messages"
 
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # "user" or "bot"
    text = db.Column(db.Text, nullable=False)
    audio_path = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
 
 
class IntentLog(db.Model):
    __tablename__ = "intent_logs"
 
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    utterance = db.Column(db.Text, nullable=False)
    predicted_intent = db.Column(db.String(64), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
 
 
class FAQEntry(db.Model):
    __tablename__ = "faq_entries"
 
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=True)
 
 
# --------------------------------------------------------------------- #
# Query helpers used by app.py
# --------------------------------------------------------------------- #
def get_or_create_conversation(session_id: str) -> Conversation:
    convo = Conversation.query.filter_by(session_id=session_id).first()
    if convo is None:
        convo = Conversation(session_id=session_id)
        db.session.add(convo)
        db.session.commit()
        logger.info("Created new conversation row for session %s", session_id)
    return convo
 
 
def log_message(conversation: Conversation, sender: str, text: str, audio_path: str = None):
    message = Message(
        conversation_id=conversation.id,
        sender=sender,
        text=text,
        audio_path=audio_path,
    )
    db.session.add(message)
    db.session.commit()
    return message
 
 
def log_intent(conversation: Conversation, utterance: str, intent: str, confidence: float):
    entry = IntentLog(
        conversation_id=conversation.id,
        utterance=utterance,
        predicted_intent=intent,
        confidence=confidence,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
 
 
def dashboard_stats() -> dict:
    """Aggregate stats used to render templates/dashboard.html."""
    total_conversations = Conversation.query.count()
    total_messages = Message.query.count()
 
    top_intents = (
        db.session.query(IntentLog.predicted_intent, db.func.count(IntentLog.id))
        .group_by(IntentLog.predicted_intent)
        .order_by(db.func.count(IntentLog.id).desc())
        .limit(10)
        .all()
    )
 
    avg_confidence = db.session.query(db.func.avg(IntentLog.confidence)).scalar() or 0.0
 
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "top_intents": top_intents,
        "avg_confidence": round(float(avg_confidence), 3),
    }
 

