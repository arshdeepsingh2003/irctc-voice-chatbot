# Handles seat availability queries.

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
    Checks what info we have, asks for what's missing — one at a time.
    """
    train_number = extracted.get("train_number")
    date         = extracted.get("date")
    travel_class = extracted.get("class")
    from_station = extracted.get("from_station")
    to_station   = extracted.get("to_station")

    # Ask for missing info — one field at a time (better UX)
    if not train_number:
        return {
            "response_text": "Sure! I can check seat availability for you. 🪑 Which train are you looking at? Please share the train number.",
            "intent": "seat_availability",
            "data_required": "train_number",
            "emotion": "friendly",
            "status": "missing_data"
        }

    if not date:
        return {
            "response_text": f"Great, train {train_number}! 📅 What date are you planning to travel? (e.g. 25 Jun 2025)",
            "intent": "seat_availability",
            "data_required": "date",
            "emotion": "friendly",
            "status": "missing_data"
        }

    if not travel_class:
        return {
            "response_text": f"Almost there! Which class do you prefer? 🚃\n• SL - Sleeper\n• 3A - Third AC\n• 2A - Second AC\n• 1A - First AC\n• CC - Chair Car",
            "intent": "seat_availability",
            "data_required": "class",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # Normalize the class
    normalized = normalize_class(travel_class)
    if not normalized:
        return {
            "response_text": f"I didn't recognize '{travel_class}' as a valid class. Please choose from: SL, 3A, 2A, 1A, CC, EC, 2S.",
            "intent": "seat_availability",
            "data_required": "class",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # All data collected — ready to fetch
    return {
        "response_text": f"Perfect! Checking {normalized} class seats on train {train_number} for {date}... 🔍",
        "intent": "seat_availability",
        "data_required": "none",
        "emotion": "friendly",
        "status": "ready",
        "train_number": train_number,
        "date": date,
        "travel_class": normalized,
        "from_station": from_station,
        "to_station": to_station
    }