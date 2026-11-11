"""FAQ retrieval plus lazy DialoGPT fallback."""
import csv
import logging
import random

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import config
from modules.dialogue_manager import DialogueAct

logger = logging.getLogger(__name__)

_GREETINGS = [
    "Hello! How can I help you today?",
    "Hi there! What can I do for you?",
    "Hey! Ask me anything.",
]
_FAREWELLS = [
    "Goodbye! Have a great day.",
    "See you soon!",
    "Bye! Feel free to come back anytime.",
]
_CLARIFICATIONS = [
    "I'm not sure I understood that. Could you rephrase your question?",
    "Sorry, could you say that a little differently?",
]
_FALLBACKS = [
    "I don't have an answer for that yet, but I'll do my best to help."
]


class KnowledgeBase:
    def __init__(self, csv_path=config.FAQ_CSV_PATH):
        self.questions = []
        self.answers = []
        self._load(csv_path)
        self.vectorizer = TfidfVectorizer()
        self._matrix = (
            self.vectorizer.fit_transform(self.questions)
            if self.questions else None
        )

    def _load(self, csv_path):
        try:
            with open(csv_path, newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    question = (row.get("question") or "").strip()
                    answer = (row.get("answer") or "").strip()
                    if question and answer:
                        self.questions.append(question)
                        self.answers.append(answer)
        except FileNotFoundError:
            logger.warning("FAQ file not found: %s", csv_path)

    def best_match(self, query):
        if not self.questions or not query.strip():
            return None, 0.0
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        idx = scores.argmax()
        return self.answers[idx], float(scores[idx])


class NeuralGenerator:
    def __init__(self, model_name=config.DIALOGPT_MODEL_NAME):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None

    def _ensure_loaded(self):
        if self._model is not None:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name)

    def generate(self, conversation_turns):
        try:
            import torch
            self._ensure_loaded()

            turns = conversation_turns[-config.DIALOGPT_MAX_HISTORY_TURNS:]
            text = self._tokenizer.eos_token.join(turns)
            input_ids = self._tokenizer.encode(
                text + self._tokenizer.eos_token,
                return_tensors="pt",
                truncation=True,
                max_length=config.DIALOGPT_MAX_INPUT_TOKENS,
            )

            output_ids = self._model.generate(
                input_ids,
                max_new_tokens=60,
                pad_token_id=self._tokenizer.eos_token_id,
                do_sample=True,
                top_p=0.9,
                temperature=0.8,
            )
            reply = self._tokenizer.decode(
                output_ids[:, input_ids.shape[-1]:][0],
                skip_special_tokens=True,
            ).strip()
            return reply or random.choice(_FALLBACKS)
        except Exception:
            logger.exception("Neural response generation failed")
            return random.choice(_FALLBACKS)


class ResponseGenerator:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.neural = NeuralGenerator()

    def generate(self, act, nlu_result, dialogue_manager):
        if act == DialogueAct.GREET:
            return random.choice(_GREETINGS)
        if act == DialogueAct.FAREWELL:
            return random.choice(_FAREWELLS)
        if act == DialogueAct.CLARIFY:
            return random.choice(_CLARIFICATIONS)
        if act == DialogueAct.FALLBACK:
            return random.choice(_FALLBACKS)

        answer, score = self.kb.best_match(nlu_result["cleaned_text"])
        if answer and score >= config.KB_MATCH_THRESHOLD:
            return answer

        return self.neural.generate(dialogue_manager.recent_user_turns())
