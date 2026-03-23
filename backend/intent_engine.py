# Detects the intent of a user's message using keyword matching.

import re

INTENT_KEYWORDS = {
    "pnr_status": [
        "pnr", "ticket status", "booking status", "pnr check",
        "check pnr", "pnr enquiry", "reservation status"
    ],
    "train_status": [
        "train status", "running status", "live train",
        "where is train", "track train", "train location",
        "train running", "status of train"
    ],
    "seat_availability": [
        "seat availability", "availability", "available seats",
        "check seats", "book ticket", "ticket booking",
        "quota", "seats left"
    ]
}


def detect_intent(message: str) -> dict:
    msg = message.lower().strip()

    # --- PNR Status ---
    if any(keyword in msg for keyword in INTENT_KEYWORDS["pnr_status"]):
        pnr_match = re.search(r'\b\d{10}\b', msg)
        pnr_number = pnr_match.group() if pnr_match else None

        return {
            "intent": "pnr_status",
            "data_required": "pnr_number",
            "extracted": {"pnr_number": pnr_number},
            "missing": [] if pnr_number else ["pnr_number"]
        }

    # --- Train Status ---
    if any(keyword in msg for keyword in INTENT_KEYWORDS["train_status"]):
        train_match = re.search(r'\b\d{4,5}\b', msg)
        train_number = train_match.group() if train_match else None

        return {
            "intent": "train_status",
            "data_required": "train_number",
            "extracted": {"train_number": train_number},
            "missing": [] if train_number else ["train_number"]
        }

    # --- Seat Availability ---
    if any(keyword in msg for keyword in INTENT_KEYWORDS["seat_availability"]):
        return {
            "intent": "seat_availability",
            "data_required": "train_number, date, class",
            "extracted": {},
            "missing": ["train_number", "date", "class"]
        }

    # --- Fallback ---
    return {
        "intent": "general_query",
        "data_required": "none",
        "extracted": {},
        "missing": []
    }