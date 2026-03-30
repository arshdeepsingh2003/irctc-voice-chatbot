from ollama_client import ask_ollama
import re

# 🔥 Improved date fallback
def extract_date_fallback(text: str):
    text = text.lower()

    # Match: 9 april 2026 OR 9 april
    match = re.search(
        r'(\d{1,2})\s*(jan|feb|mar|apr|april|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})?',
        text
    )
    if match:
        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        if year:
            return f"{day} {month} {year}"
        else:
            return f"{day} {month}"

    # Match: 26/04/2026 or 26-04-2026
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # Words
    if "tomorrow" in text:
        return "tomorrow"
    if "today" in text:
        return "today"

    return None


# ✅ UPDATED: added memory_context
def detect_intent(message: str,
                  conversation_history: list = None,
                  memory_context: str = "") -> dict:

    # ✅ pass memory_context to ollama
    result = ask_ollama(message, conversation_history, memory_context)

    intent = result.get("intent", "general_query")
    extracted = result.get("extracted", {}) or {}

    # ✅ Ensure dict
    if not isinstance(extracted, dict):
        extracted = {}

    # 🔥 DATE fallback
    if not extracted.get("date"):
        fallback_date = extract_date_fallback(message)
        if fallback_date:
            extracted["date"] = fallback_date

    # 🔥 TRAIN NUMBER fallback (SAFE)
    if not extracted.get("train_number"):
        match = re.findall(r'\b\d{4,5}\b', message)

        # remove year-like values
        match = [m for m in match if m not in ["2024", "2025", "2026", "2027"]]

        if match:
            extracted["train_number"] = match[0]

    # 🔥 CLASS fallback
    if not extracted.get("class"):
        classes = ["sl", "3a", "2a", "1a", "cc", "2s"]
        for c in classes:
            if c in message.lower():
                extracted["class"] = c.upper()

    # ✅ Update
    result["extracted"] = extracted

    # ── Missing fields logic ──
    missing = []

    if intent == "pnr_status":
        if not extracted.get("pnr_number"):
            missing.append("pnr_number")

    elif intent == "train_status":
        if not extracted.get("train_number"):
            missing.append("train_number")

    elif intent == "seat_availability":
        if not extracted.get("train_number"):
            missing.append("train_number")
        if not extracted.get("date"):
            missing.append("date")
        if not extracted.get("class"):
            missing.append("class")

    result["missing"] = missing

    print("=== FINAL EXTRACTED (ENGINE) ===")
    print(extracted)

    return result