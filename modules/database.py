"""SQLAlchemy models and database helpers."""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(64), unique=True, nullable=False, index=True
    )
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    messages = db.relationship(
        "Message", backref="conversation",
        lazy=True, cascade="all, delete-orphan"
    )
    intents = db.relationship(
        "IntentLog", backref="conversation",
        lazy=True, cascade="all, delete-orphan"
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.id"), nullable=False
    )
    sender = db.Column(db.String(10), nullable=False)
    text = db.Column(db.Text, nullable=False)
    audio_path = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class IntentLog(db.Model):
    __tablename__ = "intent_logs"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.id"), nullable=False
    )
    utterance = db.Column(db.Text, nullable=False)
    predicted_intent = db.Column(db.String(64), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def get_or_create_conversation(session_id):
    conversation = Conversation.query.filter_by(
        session_id=session_id
    ).first()
    if conversation is None:
        conversation = Conversation(session_id=session_id)
        db.session.add(conversation)
        db.session.commit()
    return conversation


def log_message(conversation, sender, text, audio_path=None):
    message = Message(
        conversation_id=conversation.id,
        sender=sender,
        text=text,
        audio_path=audio_path,
    )
    db.session.add(message)
    db.session.commit()
    return message


def log_intent(conversation, utterance, intent, confidence):
    entry = IntentLog(
        conversation_id=conversation.id,
        utterance=utterance,
        predicted_intent=intent,
        confidence=confidence,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def dashboard_stats():
    total_conversations = Conversation.query.count()
    total_messages = Message.query.count()

    top_intents = (
        db.session.query(
            IntentLog.predicted_intent,
            db.func.count(IntentLog.id),
        )
        .group_by(IntentLog.predicted_intent)
        .order_by(db.func.count(IntentLog.id).desc())
        .limit(10)
        .all()
    )

    avg_confidence = (
        db.session.query(db.func.avg(IntentLog.confidence)).scalar()
        or 0.0
    )

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "top_intents": top_intents,
        "avg_confidence": round(float(avg_confidence), 3),
    }
