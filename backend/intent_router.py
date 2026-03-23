# intent_router.py
# Routes detected intent to the correct handler.
# Safer version — does not override Ollama's intent based on response text.

from handlers.pnr_handler     import handle_pnr
from handlers.train_handler   import handle_train_status
from handlers.seat_handler    import handle_seat_availability
from handlers.general_handler import handle_general


def route_intent(intent_result: dict) -> dict:
    """
    Routes the intent_result from Ollama to the correct handler.
    Priority: extracted data > declared intent > fallback
    """
    intent      = intent_result.get("intent", "general_query")
    extracted   = intent_result.get("extracted", {})
    ollama_text = intent_result.get("response_text", "")

    # ── Smart re-routing based on EXTRACTED DATA only (not response text) ──
    # This is safer than scanning response text which can contain any word.

    pnr_number   = extracted.get("pnr_number")
    train_number = extracted.get("train_number")

    # If Ollama gave wrong intent but extracted a train number
    # AND the declared intent is general → fix it
    if intent == "general_query" and train_number:
        intent = "train_status"

    # If Ollama gave wrong intent but extracted a PNR number
    # AND the declared intent is general → fix it
    if intent == "general_query" and pnr_number:
        intent = "pnr_status"

    # ── Route to correct handler ──
    if intent == "pnr_status":
        return handle_pnr(extracted)

    elif intent == "train_status":
        return handle_train_status(extracted)

    elif intent == "seat_availability":
        return handle_seat_availability(extracted)

    else:
        return handle_general(extracted, ollama_text)