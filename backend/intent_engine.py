# Detects the intent of a user's message using keyword matching.

# intent_engine.py
# Now uses Ollama LLM for intent detection instead of keywords.

from ollama_client import ask_ollama

def detect_intent(message: str, conversation_history: list = None) -> dict:
    """
    Uses Ollama to understand the user's message and extract intent.
    Falls back gracefully if Ollama is unavailable.
    """
    result = ask_ollama(message, conversation_history)
    
    # Normalize: make sure 'missing' field exists for response_builder
    extracted = result.get("extracted", {})
    intent = result.get("intent", "general_query")
    missing = []

    if intent == "pnr_status":
        if not extracted.get("pnr_number"):
            missing.append("pnr_number")

    elif intent == "train_status":
        if not extracted.get("train_number"):
            missing.append("train_number")

    elif intent == "seat_availability":
        if not extracted.get("train_number"):
            missing.append("train_number")
        if not extracted.get("date"):
            missing.append("date")
        if not extracted.get("class"):
            missing.append("class")

    result["missing"] = missing
    return result