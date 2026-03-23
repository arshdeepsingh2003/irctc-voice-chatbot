# Handles general queries — uses Ollama's free-form response.

def handle_general(extracted: dict, ollama_response_text: str) -> dict:
    if ollama_response_text and ollama_response_text.strip():
        # If it sounds like an error message, replace it
        error_phrases = ["didn't catch", "rephrase", "don't understand", "cannot process"]
        if any(p in ollama_response_text.lower() for p in error_phrases):
            return {
                "response_text": "Namaste! 🙏 I'm your IRCTC assistant. I can help you with:\n\n• 🎫 PNR Status\n• 🚂 Live Train Status\n• 🪑 Seat Availability\n\nWhat would you like to check?",
                "intent": "general_query",
                "data_required": "none",
                "emotion": "friendly",
                "status": "ok"
            }
        return {
            "response_text": ollama_response_text,
            "intent": "general_query",
            "data_required": "none",
            "emotion": "friendly",
            "status": "ok"
        }

    return {
        "response_text": "Namaste! 🙏 I'm your IRCTC assistant. I can help you with:\n\n• 🎫 PNR Status\n• 🚂 Live Train Status\n• 🪑 Seat Availability\n\nWhat would you like to check?",
        "intent": "general_query",
        "data_required": "none",
        "emotion": "friendly",
        "status": "ok"
    }