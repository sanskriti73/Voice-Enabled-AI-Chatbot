import os
import logging

from google import genai
from config import Config

logger = logging.getLogger(__name__)

# Initialize Google Genai AI SDK if API Key is available
client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None
GEMINI_MODEL_NAME = "gemini-3.6-flash"

# Rule-Based Intent Fallback Dictionary
FALLBACK_RESPONSES = {
    "greet me": "Hello! I am your Voice-Enabled AI Assistant. How can I assist you today?",
    "hello": "Hi there! I am listening. What can I do for you?",
    "hi": "Hello! Feel free to type or speak your query.",
    "who are you": "I am a real-time Voice-Enabled AI Chatbot developed as a final year capstone project.",
    "help": "You can type a message in the input box or click the microphone button to speak with me."
}

def generate_ai_response(user_input, is_audio: bool = False) -> str:
    """
    Generates a context-aware conversational response using Gemini LLM
    or falls back to resilient rule-based matching.

    :param user_input: Text query string OR raw PCM audio bytes.
    :param is_audio: Boolean flag indicating if input is audio binary data.
    :return: Formatted conversational response string.
    """
    # Case 1: Audio Input Processing
    if is_audio:
        # When PCM audio is provided, it can be passed to multimodal Gemini or fallback transcribed
        logger.info("Processing voice audio stream for LLM inference...")
        if client:
            try:
                # Multimodal audio payload for Gemini
                audio_part = {
                    "mime_type": "audio/pcm",
                    "data": user_input
                }
                response = client.models.generate_content(
                    model=GEMINI_MODEL_NAME,
                    contents=[
                        "Listen to this spoken query and reply directly to the user:",
                        audio_part
                    ]
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini multimodal audio inference failed: {str(e)}")
                return "I received your voice message, but I encountered an issue analyzing the audio stream."
        else:
            return "Voice received successfully, but Gemini API is currently offline."

    # Case 2: Text Input Processing
    cleaned_text = str(user_input).strip()
    lookup_key = cleaned_text.lower()

    # Check rule-based fast lookup first for instant replies
    if lookup_key in FALLBACK_RESPONSES:
        return FALLBACK_RESPONSES[lookup_key]

    # Query Gemini Foundation Model
    if client:
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=cleaned_text
            )
            if response and response.text:
                return response.text.strip()
            else:
                return "I processed your request, but received an empty response. Please try rephrasing."
        except Exception as e:
            logger.error(f"Gemini API generation error: {str(e)}")
            # Graceful contextual fallback rather than crashing
            return "I don't have an answer for that yet, but I'll do my best to help if you rephrase."

    # Offline Default Fallback
    return "I don't have an answer for that yet, but I'll do my best to help."
