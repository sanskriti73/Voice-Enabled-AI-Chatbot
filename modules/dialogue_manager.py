"""
modules/dialogue_manager.py
Finite State Machine (FSM) based dialogue manager.
 
Tracks conversation state per session_id and decides, based on the
current state plus the NLU output for the latest turn, what state to
transition to next and what "dialogue act" to hand off to the response
generator (e.g. GREET, ANSWER_FAQ, ASK_CLARIFICATION, CLOSE).
"""
 
import logging
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
    """
    One DialogueManager instance is created per active chat session and
    holds that session's FSM state + short conversational memory.
    """
 
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = DialogueState.START
        self.turn_count = 0
        self.history = []  # list of {"user":..., "bot":..., "intent":...}
        self.pending_clarification = None
 
    def step(self, nlu_result: dict) -> DialogueAct:
        """
        Advance the FSM by one turn given the NLU analysis of the user's
        latest utterance. Returns the dialogue act that response_generator
        should realize into natural language.
        """
        self.turn_count += 1
        intent = nlu_result["intent"]
        confidence = nlu_result["confidence"]
 
        logger.debug("[%s] state=%s intent=%s conf=%.2f",
                     self.session_id, self.state, intent, confidence)
 
        if intent in GREETING_INTENTS and self.state == DialogueState.START:
            self.state = DialogueState.GREETING
            act = DialogueAct.GREET
 
        elif intent in FAREWELL_INTENTS:
            self.state = DialogueState.CLOSING
            act = DialogueAct.FAREWELL
 
        elif intent == config.FALLBACK_INTENT:
            if self.state == DialogueState.CLARIFYING:
                # user still unclear after one clarification attempt -> fallback fully
                self.state = DialogueState.AWAITING_QUERY
                act = DialogueAct.FALLBACK
            else:
                self.state = DialogueState.CLARIFYING
                self.pending_clarification = nlu_result["raw_text"]
                act = DialogueAct.CLARIFY
 
        else:
            self.state = DialogueState.ANSWERING
            act = DialogueAct.ANSWER
            self.pending_clarification = None
 
        self._remember(nlu_result, act)
        return act
 
    def _remember(self, nlu_result: dict, act: DialogueAct):
        self.history.append({
            "user": nlu_result["raw_text"],
            "intent": nlu_result["intent"],
            "act": act.name,
        })
        max_turns = config.DIALOGPT_MAX_HISTORY_TURNS
        if len(self.history) > max_turns:
            self.history = self.history[-max_turns:]
 
    def recent_user_turns(self) -> list:
        """Used by response_generator to build DialoGPT conversation context."""
        return [turn["user"] for turn in self.history]
 
    def reset(self):
        self.state = DialogueState.START
        self.turn_count = 0
        self.history.clear()
        self.pending_clarification = None
 
 
class SessionRegistry:
    """In-memory registry mapping session_id -> DialogueManager."""
 
    def __init__(self):
        self._sessions = {}
 
    def get_or_create(self, session_id: str) -> DialogueManager:
        if session_id not in self._sessions:
            logger.info("Creating new dialogue session: %s", session_id)
            self._sessions[session_id] = DialogueManager(session_id)
        return self._sessions[session_id]
 
    def end_session(self, session_id: str):
        self._sessions.pop(session_id, None)
 
 
# Module-level singleton used by app.py
session_registry = SessionRegistry()

