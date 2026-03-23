# Handles train running status queries.

import re

def validate_train_number(train_number: str) -> bool:
    """A valid Indian train number is 4 or 5 digits."""
    if not train_number:
        return False
    return bool(re.fullmatch(r'\d{4,5}', str(train_number).strip()))


def handle_train_status(extracted: dict) -> dict:
    """
    Main handler for train_status intent.
    """
    train_number = extracted.get("train_number")

    # Step 1: Check if train number was provided
    if not train_number:
        return {
            "response_text": "I'll check the live running status right away! 🚂 Could you share the train number? It's a 4 or 5 digit number (e.g. 12301 for Howrah Rajdhani).",
            "intent": "train_status",
            "data_required": "train_number",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # Step 2: Validate train number
    if not validate_train_number(train_number):
        return {
            "response_text": f"'{train_number}' doesn't seem like a valid train number. 🤔 Train numbers are 4-5 digits long (e.g. 12301). Could you check and try again?",
            "intent": "train_status",
            "data_required": "train_number",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # Step 3: Valid — ready to fetch
    return {
        "response_text": f"Fetching live running status for train {train_number}... 🚦",
        "intent": "train_status",
        "data_required": "none",
        "emotion": "friendly",
        "status": "ready",
        "train_number": train_number
    }