# handlers/train_handler.py

import re
from api.railway_client import fetch_train_status
from api.api_helpers import format_train_status_response


def validate_train_number(train_number: str) -> bool:
    """A valid Indian train number is 4 or 5 digits."""
    return bool(re.fullmatch(r'\d{4,5}', str(train_number).strip()))


def handle_train_status(extracted: dict) -> dict:
    """
    Main handler for train_status intent.
    """

    train_number = extracted.get("train_number")

    # STEP 1: Missing train number
    if not train_number:
        return {
            "response_text": "I'll check the live running status right away! 🚂 Could you share the train number? It's a 4 or 5 digit number (e.g. 12301 for Howrah Rajdhani).",
            "intent": "train_status",
            "data_required": "train_number",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # STEP 2: Clean input
    train_clean = str(train_number).strip()

    # STEP 3: Validate
    if not validate_train_number(train_clean):
        return {
            "response_text": f"'{train_clean}' doesn't seem like a valid train number. 🤔 Train numbers are 4-5 digits long (e.g. 12301). Could you check and try again?",
            "intent": "train_status",
            "data_required": "train_number",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # STEP 4: Fetch data from API
    result = fetch_train_status(train_clean)

    # ───────────────── DEBUG BLOCK (TEMPORARY) ─────────────────
    import json
    print("\n================ DEBUG START ================")

    print("\n=== RAW API RESULT KEYS ===")
    print(json.dumps(list(result.keys()), indent=2))

    if result.get("data"):
        print("\n=== result['data'] type ===")
        print(type(result["data"]))

        if isinstance(result["data"], dict):
            print("\n=== result['data'] keys ===")
            print(list(result["data"].keys()))

            if result["data"].get("data"):
                inner = result["data"]["data"]

                print("\n=== result['data']['data'] type ===")
                print(type(inner))

                if isinstance(inner, dict):
                    print("\n=== result['data']['data'] keys ===")
                    print(list(inner.keys())[:20])  # first 20 keys

                    # Check deeper nesting just in case
                    if inner.get("data"):
                        print("\n=== result['data']['data']['data'] type ===")
                        print(type(inner["data"]))

                        if isinstance(inner["data"], dict):
                            print("\n=== result['data']['data']['data'] keys ===")
                            print(list(inner["data"].keys())[:10])

    print("\n================ DEBUG END =================\n")
    # ───────────────── END DEBUG ─────────────────

    # STEP 5: Handle API failure
    if not result.get("success"):
        return {
            "response_text": f"Sorry, I couldn't fetch the live status for train {train_clean} right now. 😔\nReason: {result.get('error')}\n\nThis could mean the train isn't running today, or the API is temporarily unavailable.",
            "intent": "train_status",
            "data_required": "none",
            "emotion": "friendly",
            "status": "api_error"
        }

    # STEP 6: Format response
    formatted = format_train_status_response(result.get("data"))

    return {
        "response_text": formatted,
        "intent": "train_status",
        "data_required": "none",
        "emotion": "friendly",
        "status": "success",
        "train_number": train_clean
    }