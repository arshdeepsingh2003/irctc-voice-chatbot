from app.utils.helpers import extract_train_number, extract_pnr


def handle_intent(intent: str, text: str):
    """
    Handles intent-based logic and returns structured data
    (NOT final sentences — LLM will format response)
    """

    if intent == "train_status":
        train = extract_train_number(text)

        if not train:
            return {
                "error": "missing_train_number",
                "message": "Train number not provided"
            }

        # 🔥 Mock data (replace with real API later)
        return {
            "type": "train_status",
            "train_number": train,
            "current_location": "Kanpur",
            "delay": "20 minutes",
            "next_station": "Lucknow",
            "arrival_time": "14:30"
        }

    elif intent == "pnr_status":
        pnr = extract_pnr(text)

        if not pnr:
            return {
                "error": "missing_pnr",
                "message": "PNR number not provided"
            }

        # 🔥 Mock data
        return {
            "type": "pnr_status",
            "pnr": pnr,
            "status": "Confirmed",
            "coach": "S3",
            "seat": "45",
            "berth": "Lower"
        }

    elif intent == "seat_availability":
        # 🔥 Placeholder (can expand later)
        return {
            "type": "seat_availability",
            "availability": "Available",
            "classes": ["Sleeper", "3AC"]
        }

    return None