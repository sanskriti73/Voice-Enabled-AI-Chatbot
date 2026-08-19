import ollama
from config import Config

class ResponseGenerator:
    def __init__(self):
        self.model = Config.OLLAMA_MODEL

    def generate_response(self, user_input, conversation_history=None):
        messages = conversation_history or []
        messages.append({'role': 'user', 'content': user_input})

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            return response['message']['content']
        except Exception as e:
            return f"Sorry, I couldn't generate a response right now. ({str(e)})"

"""Flow:
    1. If the dialogue act is GREET / FAREWELL / CLARIFY -> canned templates.
    2. If ANSWER -> try to match the query against the FAQ knowledge base
       using TF-IDF cosine similarity.
         - If best match score >= KB_MATCH_THRESHOLD -> return that FAQ answer.
         - Otherwise -> fall back to the DialoGPT neural generator so the
           bot still produces a plausible conversational reply.
"""
 
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
    "I'm not sure I understood that — could you rephrase your question?",
    "Sorry, could you say that a little differently?",
]
_FALLBACKS = [
    "I don't have an answer for that yet, but I'll do my best to help.",
]
 
 
class KnowledgeBase:
    """TF-IDF backed FAQ lookup, loaded from datasets/faq_seed.csv."""
 
    def __init__(self, csv_path: str = config.FAQ_CSV_PATH):
        self.questions, self.answers = [], []
        self._load(csv_path)
        self.vectorizer = TfidfVectorizer()
        self._matrix = self.vectorizer.fit_transform(self.questions) if self.questions else None
 
    def _load(self, csv_path: str):
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.questions.append(row["question"])
                    self.answers.append(row["answer"])
            logger.info("Loaded %d FAQ entries from %s", len(self.questions), csv_path)
        except FileNotFoundError:
            logger.warning("FAQ file %s not found; KB will be empty.", csv_path)
 
    def best_match(self, query: str):
        """Returns (answer: str or None, score: float)."""
        if not self.questions:
            return None, 0.0
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._matrix)[0]
        best_idx = sims.argmax()
        return self.answers[best_idx], float(sims[best_idx])
 
 
class NeuralGenerator:
    """Lazy-loaded DialoGPT wrapper for open-domain fallback responses."""
 
    def __init__(self, model_name: str = config.DIALOGPT_MODEL_NAME):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
 
    def _ensure_loaded(self):
        if self._model is None:
            import torch  # noqa: F401 (imported lazily; heavy dependency)
            from transformers import AutoModelForCausalLM, AutoTokenizer
 
            logger.info("Loading DialoGPT model '%s' (first use only)...", self.model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
 
    def generate(self, conversation_turns: list) -> str:
        self._ensure_loaded()
        import torch
 
        input_ids = None
        for turn in conversation_turns:
            new_ids = self._tokenizer.encode(turn + self._tokenizer.eos_token, return_tensors="pt")
            input_ids = new_ids if input_ids is None else torch.cat([input_ids, new_ids], dim=-1)
 
        output_ids = self._model.generate(
            input_ids,
            max_length=input_ids.shape[-1] + 60,
            pad_token_id=self._tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.9,
            temperature=0.8,
        )
        reply = self._tokenizer.decode(
            output_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True
        )
        return reply.strip() or random.choice(_FALLBACKS)
 
 
class ResponseGenerator:
    """Combines canned templates, KB lookup, and the neural fallback."""
 
    def __init__(self):
        self.kb = KnowledgeBase()
        self.neural = NeuralGenerator()
 
    def generate(self, act: DialogueAct, nlu_result: dict, dialogue_manager) -> str:
        if act == DialogueAct.GREET:
            return random.choice(_GREETINGS)
        if act == DialogueAct.FAREWELL:
            return random.choice(_FAREWELLS)
        if act == DialogueAct.CLARIFY:
            return random.choice(_CLARIFICATIONS)
 
        if act == DialogueAct.ANSWER:
            answer, score = self.kb.best_match(nlu_result["cleaned_text"])
            logger.debug("KB best match score=%.2f", score)
            if answer and score >= config.KB_MATCH_THRESHOLD:
                return answer
            # Fall back to neural generation using recent conversation context
            turns = dialogue_manager.recent_user_turns()
            return self.neural.generate(turns)
 
        # act == DialogueAct.FALLBACK
        return random.choice(_FALLBACKS)
