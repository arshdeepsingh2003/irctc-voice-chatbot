# intent_router.py

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

    pnr_number   = extracted.get("pnr_number")
    train_number = extracted.get("train_number")
    date         = extracted.get("date")
    travel_class = extracted.get("class")
    from_station = extracted.get("from_station")
    to_station   = extracted.get("to_station")

    # ── FIX 1: Seat flow continuation (MOST IMPORTANT) ──
    if intent == "general_query":
        if any([train_number, date, travel_class, from_station, to_station]):
            intent = "seat_availability"

    # ── FIX 2: Existing smart rerouting ──
    if intent == "general_query" and train_number:
        intent = "train_status"

    if intent == "general_query" and pnr_number:
        intent = "pnr_status"

    # ── Route ──
    if intent == "pnr_status":
        return handle_pnr(extracted)

    elif intent == "train_status":
        return handle_train_status(extracted)

    elif intent == "seat_availability":
        return handle_seat_availability(extracted)

    else:
        return handle_general(extracted, ollama_text)