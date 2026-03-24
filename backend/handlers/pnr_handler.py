# handlers/pnr_handler.py

import re
from api.railway_client import fetch_pnr_status
from api.api_helpers import format_pnr_response


def validate_pnr(pnr: str) -> bool:
    """A valid PNR is exactly 10 digits."""
    return bool(re.fullmatch(r"\d{10}", str(pnr).strip()))


def extract_pnr_from_text(text: str) -> str | None:
    """
    Extracts a 10-digit PNR directly from raw user message.
    This avoids LLM hallucination / context leakage.
    """
    if not text:
        return None

    matches = re.findall(r"\d{10}", text)
    return matches[0] if matches else None


def handle_pnr(extracted: dict, user_message: str = "") -> dict:
    """
    Main handler for pnr_status intent.

    extracted: dict from Ollama
    user_message: raw user input (VERY IMPORTANT for accuracy)
    """

    # 🔥 STEP 1: Extract from USER MESSAGE (highest priority)
    pnr_from_text = extract_pnr_from_text(user_message)

    # 🔥 STEP 2: fallback to LLM extracted value
    raw_pnr = pnr_from_text or extracted.get("pnr_number")

    # STEP 3: Missing PNR
    if not raw_pnr:
        return {
            "response_text": "I'd be happy to check your PNR status! 🎫 Could you please share your 10-digit PNR number?",
            "intent": "pnr_status",
            "data_required": "pnr_number",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # STEP 4: Clean input
    pnr_clean = re.sub(r"\D", "", str(raw_pnr))

    # STEP 5: Validate
    if not validate_pnr(pnr_clean):
        return {
            "response_text": "That doesn't look like a valid PNR number. 🤔 A PNR must be exactly 10 digits. Please recheck and send again.",
            "intent": "pnr_status",
            "data_required": "pnr_number",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # ── NEW: Fetch real data from API ──
    result = fetch_pnr_status(pnr_clean)

    if not result.get("success"):
        return {
            "response_text": f"Sorry, I couldn't fetch PNR status right now. 😔\nReason: {result.get('error')}\n\nPlease try again in a moment.",
            "intent": "pnr_status",
            "data_required": "none",
            "emotion": "friendly",
            "status": "api_error"
        }

    # ── Format response ──
    formatted = format_pnr_response(result.get("data"))

    return {
        "response_text": formatted,
        "intent": "pnr_status",
        "data_required": "none",
        "emotion": "friendly",
        "status": "success",
        "pnr_number": pnr_clean
    }