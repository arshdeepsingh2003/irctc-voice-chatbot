# handlers/seat_handler.py

from api.railway_client import fetch_seat_availability
from api.api_helpers import format_seat_availability_response, parse_date_for_api

VALID_CLASSES = {
    "sl": "SL", "sleeper": "SL",
    "3a": "3A", "3ac": "3A", "third ac": "3A",
    "2a": "2A", "2ac": "2A", "second ac": "2A",
    "1a": "1A", "1ac": "1A", "first ac": "1A",
    "cc": "CC", "chair car": "CC",
    "ec": "EC", "executive": "EC",
    "2s": "2S", "second sitting": "2S"
}


def normalize_class(raw_class: str) -> str | None:
    """Converts user input like '3ac' or 'sleeper' to standard code."""
    if not raw_class:
        return None
    return VALID_CLASSES.get(raw_class.lower().strip())


def handle_seat_availability(extracted: dict) -> dict:
    """
    Main handler for seat_availability intent.
    """

    train_number = extracted.get("train_number")
    date         = extracted.get("date")
    travel_class = extracted.get("class")
    from_station = extracted.get("from_station")
    to_station   = extracted.get("to_station")

    # STEP 1: Train number
    if not train_number:
        return {
            "response_text": "Sure! I can check seat availability for you. 🪑 Which train are you looking at? Please share the train number.",
            "intent": "seat_availability",
            "data_required": "train_number",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # STEP 2: Date
    if not date:
        return {
            "response_text": f"Great, train {train_number}! 📅 What date are you planning to travel? (e.g. 25 Jun 2025)",
            "intent": "seat_availability",
            "data_required": "date",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # STEP 3: Class
    if not travel_class:
        return {
            "response_text": f"Almost there! Which class do you prefer? 🚃\n• SL - Sleeper\n• 3A - Third AC\n• 2A - Second AC\n• 1A - First AC\n• CC - Chair Car",
            "intent": "seat_availability",
            "data_required": "class",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # STEP 4: Normalize class
    normalized = normalize_class(travel_class)
    if not normalized:
        return {
            "response_text": f"I didn't recognize '{travel_class}' as a valid class. Please choose from: SL, 3A, 2A, 1A, CC, EC, 2S.",
            "intent": "seat_availability",
            "data_required": "class",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # 🔥 NEW (but safe): Ask for stations if missing
    if not from_station or not to_station:
        return {
            "response_text": f"One last thing! 🛤️ What's your boarding station and destination station code? (e.g. NDLS for New Delhi, BCT for Mumbai Central)",
            "intent": "seat_availability",
            "data_required": "from_station, to_station",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # 🔥 NEW: Date parsing for API
    api_date = parse_date_for_api(date)
    if not api_date:
        return {
            "response_text": f"I had trouble reading the date '{date}'. Could you share it in a clear format like '25 Jun 2025'?",
            "intent": "seat_availability",
            "data_required": "date",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # ── Fetch real data from API ──
    result = fetch_seat_availability(
        train_number=train_number,
        date=api_date,
        from_station=from_station.upper(),
        to_station=to_station.upper(),
        travel_class=normalized
    )

    if not result.get("success"):
        return {
            "response_text": f"Sorry, couldn't fetch seat availability right now. 😔\nReason: {result.get('error')}",
            "intent": "seat_availability",
            "data_required": "none",
            "emotion": "friendly",
            "status": "api_error"
        }

    # ── Format response ──
    formatted = format_seat_availability_response(result.get("data"))

    return {
        "response_text": formatted,
        "intent": "seat_availability",
        "data_required": "none",
        "emotion": "friendly",
        "status": "success",
        "train_number": train_number,
        "date": api_date,
        "travel_class": normalized,
        "from_station": from_station.upper(),
        "to_station": to_station.upper()
    }