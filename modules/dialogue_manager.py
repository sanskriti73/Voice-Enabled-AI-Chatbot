"""FSM dialogue manager with bounded user/bot conversational history."""
import logging
import time
from enum import Enum, auto

import config

logger = logging.getLogger(__name__)


class DialogueState(Enum):
    START = auto()
    GREETING = auto()
    AWAITING_QUERY = auto()
    CLARIFYING = auto()
    ANSWERING = auto()
    CLOSING = auto()


class DialogueAct(Enum):
    GREET = auto()
    ANSWER = auto()
    CLARIFY = auto()
    FALLBACK = auto()
    FAREWELL = auto()


GREETING_INTENTS = {"greeting", "hello"}
FAREWELL_INTENTS = {"goodbye", "bye", "exit"}


class DialogueManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = DialogueState.START
        self.turn_count = 0
        self.history = []
        self.pending_clarification = None
        self.last_activity = time.monotonic()

    def step(self, nlu_result: dict) -> DialogueAct:
        self.turn_count += 1
        self.last_activity = time.monotonic()

        intent = nlu_result["intent"]

        if intent in GREETING_INTENTS and self.state == DialogueState.START:
            self.state = DialogueState.GREETING
            act = DialogueAct.GREET
        elif intent in FAREWELL_INTENTS:
            self.state = DialogueState.CLOSING
            act = DialogueAct.FAREWELL
        elif intent == config.FALLBACK_INTENT:
            if self.state == DialogueState.CLARIFYING:
                self.state = DialogueState.AWAITING_QUERY
                act = DialogueAct.FALLBACK
            else:
                self.state = DialogueState.CLARIFYING
                self.pending_clarification = nlu_result["raw_text"]
                act = DialogueAct.CLARIFY
        else:
            self.state = DialogueState.ANSWERING
            self.pending_clarification = None
            act = DialogueAct.ANSWER

        self._remember_user_turn(nlu_result, act)
        return act

    def _remember_user_turn(self, nlu_result, act):
        self.history.append({
            "user": nlu_result["raw_text"],
            "bot": None,
            "intent": nlu_result["intent"],
            "act": act.name,
        })
        self._cap_history()

    def remember_bot_response(self, bot_text: str):
        if self.history:
            self.history[-1]["bot"] = bot_text
        self.last_activity = time.monotonic()

    def _cap_history(self):
        self.history = self.history[-config.DIALOGPT_MAX_HISTORY_TURNS:]

    def recent_user_turns(self):
        turns = []
        for turn in self.history:
            if turn["user"]:
                turns.append(turn["user"])
            if turn["bot"]:
                turns.append(turn["bot"])
        return turns

    def reset(self):
        self.state = DialogueState.START
        self.turn_count = 0
        self.history.clear()
        self.pending_clarification = None
        self.last_activity = time.monotonic()


class SessionRegistry:
    def __init__(self, ttl_seconds=3600):
        self._sessions = {}
        self.ttl_seconds = ttl_seconds

    def _cleanup(self):
        now = time.monotonic()
        stale = [
            sid for sid, manager in self._sessions.items()
            if now - manager.last_activity > self.ttl_seconds
        ]
        for sid in stale:
            self._sessions.pop(sid, None)

    def get_or_create(self, session_id: str):
        self._cleanup()
        if session_id not in self._sessions:
            self._sessions[session_id] = DialogueManager(session_id)
        return self._sessions[session_id]

    def end_session(self, session_id: str):
        self._sessions.pop(session_id, None)


session_registry = SessionRegistry()
