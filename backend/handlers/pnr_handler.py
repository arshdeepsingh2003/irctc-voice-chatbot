# Handles all PNR status related queries.

import re


def validate_pnr(pnr: str) -> bool:
    """A valid PNR is exactly 10 digits."""
    if not pnr:
        return False
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

    Returns a response dict.
    """

    # 🔥 STEP 1: Try extracting from USER MESSAGE (highest priority)
    pnr_from_text = extract_pnr_from_text(user_message)

    # 🔥 STEP 2: fallback to extracted (LLM output)
    raw_pnr = pnr_from_text or extracted.get("pnr_number")

    # STEP 3: If nothing found → ask user
    if not raw_pnr:
        return {
            "response_text": "I'd be happy to check your PNR status! 🎫 Could you please share your 10-digit PNR number?",
            "intent": "pnr_status",
            "data_required": "pnr_number",
            "emotion": "friendly",
            "status": "missing_data"
        }

    # STEP 4: Clean input (remove non-digits)
    pnr_clean = re.sub(r"\D", "", str(raw_pnr))

    # 🚨 CRITICAL CHECK: Must be EXACTLY 10 digits
    if len(pnr_clean) != 10:
        return {
            "response_text": f"That doesn't look like a valid PNR number. 🤔 A PNR must be exactly 10 digits. Please recheck and send again.",
            "intent": "pnr_status",
            "data_required": "pnr_number",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # STEP 5: Final validation
    if not validate_pnr(pnr_clean):
        return {
            "response_text": "Invalid PNR format. Please enter a valid 10-digit number.",
            "intent": "pnr_status",
            "data_required": "pnr_number",
            "emotion": "friendly",
            "status": "invalid_data"
        }

    # STEP 6: Ready for API fetch (next phase)
    return {
        "response_text": f"Got it! Checking PNR {pnr_clean} for you right now... 🔍",
        "intent": "pnr_status",
        "data_required": "none",
        "emotion": "friendly",
        "status": "ready",
        "pnr_number": pnr_clean
    }