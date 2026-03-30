# Handles general queries — uses Ollama's free-form response.

from ollama_client import humanize_response  # ✅ NEW

def handle_general(extracted: dict,
                   ollama_response_text: str,
                   memory_context: str = "") -> dict:   # ✅ UPDATED

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

        # ✅ NEW: Humanize with memory
        human_reply = humanize_response(
            raw_data_text=ollama_response_text,
            intent="general_query",
            context="General conversation",
            memory_context=memory_context
        )

        return {
            "response_text": human_reply,
            "intent": "general_query",
            "data_required": "none",
            "emotion": "friendly",
            "status": "ok"
        }

    return {
        "response_text": "Namaste!  I'm your IRCTC assistant. I can help you with:\n\n• 🎫 PNR Status\n• 🚂 Live Train Status\n• 🪑 Seat Availability\n\nWhat would you like to check?",
        "intent": "general_query",
        "data_required": "none",
        "emotion": "friendly",
        "status": "ok"
    }