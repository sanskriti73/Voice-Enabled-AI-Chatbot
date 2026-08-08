"""
tests/test_dialogue.py
Unit tests for the FSM-based dialogue manager in modules/dialogue_manager.py.
"""
 
import pytest
 
from modules.dialogue_manager import DialogueManager, DialogueAct, DialogueState
import config
 
 
def nlu_result(intent, confidence=0.9, text="sample"):
    return {"raw_text": text, "cleaned_text": text, "intent": intent, "confidence": confidence, "entities": {}}
 
 
def test_greeting_transitions_to_greeting_state():
    dm = DialogueManager("session-1")
    act = dm.step(nlu_result("greeting"))
    assert act == DialogueAct.GREET
    assert dm.state == DialogueState.GREETING
 
 
def test_farewell_transitions_to_closing_state():
    dm = DialogueManager("session-2")
    act = dm.step(nlu_result("goodbye"))
    assert act == DialogueAct.FAREWELL
    assert dm.state == DialogueState.CLOSING
 
 
def test_fallback_then_fallback_again_triggers_full_fallback():
    dm = DialogueManager("session-3")
    first_act = dm.step(nlu_result(config.FALLBACK_INTENT, confidence=0.2))
    assert first_act == DialogueAct.CLARIFY
    assert dm.state == DialogueState.CLARIFYING
 
    second_act = dm.step(nlu_result(config.FALLBACK_INTENT, confidence=0.2))
    assert second_act == DialogueAct.FALLBACK
 
 
def test_known_intent_transitions_to_answering():
    dm = DialogueManager("session-4")
    act = dm.step(nlu_result("library_hours"))
    assert act == DialogueAct.ANSWER
    assert dm.state == DialogueState.ANSWERING
 
 
def test_history_is_capped_at_max_turns():
    dm = DialogueManager("session-5")
    for i in range(config.DIALOGPT_MAX_HISTORY_TURNS + 5):
        dm.step(nlu_result("library_hours", text=f"turn {i}"))
    assert len(dm.history) == config.DIALOGPT_MAX_HISTORY_TURNS


