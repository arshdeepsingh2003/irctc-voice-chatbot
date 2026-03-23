# response_builder.py
# Builds a friendly response based on the detected intent.
# In Phase 6, this will use Ollama to generate natural language.

MISSING_INFO_PROMPTS = {
    "pnr_number": "Could you please share your 10-digit PNR number? I'll check the status right away! 🎫",
    "train_number": "Sure! Which train are you asking about? Please share the train number. 🚂",
    "date": "Which date are you travelling on? (e.g. 25 Jun 2025)",
    "class": "Which class are you looking for? (e.g. Sleeper, 3AC, 2AC, 1AC)",
}

INTENT_RESPONSES = {
    "pnr_status": "I found your PNR! Let me fetch the latest status for you. 🔍",
    "train_status": "Let me check the live running status of your train right now! 🚂",
    "seat_availability": "Let me check seat availability for you. 🪑",
    "general_query": "I'm your IRCTC assistant! I can help you with PNR status, train running status, and seat availability. What would you like to know? 😊",
}

def build_response(intent_result: dict, user_message: str) -> dict:
    intent = intent_result["intent"]
    missing = intent_result.get("missing", [])

    # If required information is missing, ask for it
    if missing:
        missing_field = missing[0]  # Ask for one thing at a time
        response_text = MISSING_INFO_PROMPTS.get(
            missing_field,
            f"Could you share the {missing_field.replace('_', ' ')}?"
        )
        return {
            "response_text": response_text,
            "intent": intent,
            "data_required": intent_result.get("data_required", "none"),
            "emotion": "friendly"
        }

    # All info is available — confirm we're processing
    response_text = INTENT_RESPONSES.get(intent, "I'm here to help! What would you like to know?")

    return {
        "response_text": response_text,
        "intent": intent,
        "data_required": intent_result.get("data_required", "none"),
        "emotion": "friendly"
    }