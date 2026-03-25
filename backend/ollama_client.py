import httpx
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL_NAME = os.getenv("OLLAMA_MODEL")


# 🔥 FINAL SYSTEM PROMPT (STRICT + SAFE)
SYSTEM_PROMPT = """You are an IRCTC railway assistant. Respond ONLY in valid JSON.

STRICT INTENT RULES — no exceptions:

"seat_availability" triggers when user says ANY of:
  - seats, seat, availability, available, book, booking, check seats,
    want to check seats, I want to check, want to book, coach

"train_status" triggers when user says ANY of:
  - where is train, live status, running status, is train running,
    train location, train number (ONLY if previous intent was train_status)

"pnr_status" triggers when user says ANY of:
  - pnr, ticket status, booking status, passenger status

"general_query" triggers for:
  - hello, hi, thanks, help, what can you do, anything else

EXAMPLES — memorize these:
  "I want to check seats"        → seat_availability
  "check seat availability"      → seat_availability
  "any seats on train 12301"     → seat_availability
  "seats in sleeper"             → seat_availability
  "where is train 12301"         → train_status
  "live status of 12301"         → train_status
  "check PNR 1234567890"         → pnr_status
  "hello"                        → general_query

EXTRACTION RULES:
  - Only extract values explicitly stated in THIS message
  - Never reuse values from previous messages
  - If not stated → set null
  - A train_number is ONLY 4-5 digits when it appears ALONE or after the word "train"
  - NEVER extract a year like 2025 or 2026 as a train_number
  - Date patterns like "26 April 2026", "25 Jun 2025", "26/04/2026" → always set as "date", never train_number
  - If message is ONLY a date like "26 April 2026" → date = "26 April 2026", train_number = null

DATE EXTRACTION EXAMPLES — memorize:
  "26 April 2026"     → date = "26 April 2026",  train_number = null
  "25 Jun 2025"       → date = "25 Jun 2025",    train_number = null
  "travel on 1 May"   → date = "1 May",          train_number = null
  "train 12301"       → train_number = "12301",  date = null
  "12301 on 25 June"  → train_number = "12301",  date = "25 June"

RESPONSE FORMAT — always this exact JSON, nothing else:
{
  "response_text": "friendly reply",
  "intent": "seat_availability | train_status | pnr_status | general_query",
  "data_required": "what is needed or none",
  "emotion": "friendly",
  "extracted": {
    "pnr_number": null,
    "train_number": null,
    "date": null,
    "class": null,
    "from_station": null,
    "to_station": null
  }
}"""


# 🔥 ANTI-HALLUCINATION CLEANER (MOST IMPORTANT)
def clean_extracted_fields(extracted: dict, user_message: str) -> dict:
    text = user_message.lower()
    cleaned = dict(extracted)  # ✅ preserve previous data

    # ✅ PNR
    pnr_match = re.findall(r"\b\d{10}\b", user_message)
    if pnr_match:
        cleaned["pnr_number"] = pnr_match[0]

    # ✅ Train number (avoid years)
    train_match = re.findall(r"\b\d{4,5}\b", user_message)
    train_match = [t for t in train_match if t not in ["2024", "2025", "2026", "2027"]]
    if train_match:
        cleaned["train_number"] = train_match[0]

    # 🔥 DATE (ONLY UPDATE IF FOUND)
    date_patterns = [
        r'\b\d{1,2}\s*(jan|feb|mar|apr|april|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{0,4}',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
    ]

    date_found = None

    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_found = match.group()
            break

    if "today" in text:
        date_found = "today"
    elif "tomorrow" in text:
        date_found = "tomorrow"

    if date_found:
        cleaned["date"] = date_found  # ✅ ONLY if found

    # ✅ Class
    classes = ["sl", "3a", "2a", "1a", "cc", "2s"]
    found_class = next((c.upper() for c in classes if c in text), None)
    if found_class:
        cleaned["class"] = found_class

    # 🔥 STATIONS (ONLY UPDATE IF FOUND)
    station_match = re.search(r'\b([A-Z]{3,5})\s+to\s+([A-Z]{3,5})\b', user_message.upper())

    if station_match:
        cleaned["from_station"] = station_match.group(1)
        cleaned["to_station"] = station_match.group(2)
    else:
        from_match = re.search(r'from\s+([A-Z]{3,5})', user_message.lower())
        to_match = re.search(r'to\s+([A-Z]{3,5})', user_message.lower())

        if from_match:
            cleaned["from_station"] = from_match.group(1).upper()
        if to_match:
            cleaned["to_station"] = to_match.group(1).upper()

    return cleaned


def ask_ollama(user_message: str, conversation_history: list = None) -> dict:
    history_text = ""
    if conversation_history:
        for turn in conversation_history[-4:]:
            role = "User" if turn["role"] == "user" else "Assistant"
            history_text += f"{role}: {turn['content']}\n"

    full_prompt = f"{history_text}User: {user_message}\nAssistant:"

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "top_p": 0.9
        }
    }

    try:
        for attempt in range(2):
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(OLLAMA_URL, json=payload)
                    response.raise_for_status()
                break
            except httpx.TimeoutException:
                if attempt == 1:
                    return fallback_response("Server timeout. Please try again.")
                continue

        result = response.json()
        raw_text = result.get("response", "")

        parsed = parse_ollama_response(raw_text)

        parsed["extracted"] = clean_extracted_fields(
            parsed.get("extracted", {}),
            user_message
        )

        return parsed

    except httpx.ConnectError:
        return fallback_response("Ollama is not running. Start using: ollama serve")
    except Exception as e:
        return fallback_response(f"Error: {str(e)}")


def parse_ollama_response(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    raw_text = re.sub(r"```json\s*", "", raw_text)
    raw_text = re.sub(r"```\s*", "", raw_text)

    try:
        data = json.loads(raw_text)
        return {
            "response_text": data.get("response_text", "I'm here to help!"),
            "intent": data.get("intent", "general_query"),
            "data_required": data.get("data_required", "none"),
            "emotion": data.get("emotion", "friendly"),
            "extracted": data.get("extracted", {})
        }
    except json.JSONDecodeError:
        return fallback_response("I couldn't understand that. Please try again.")


def fallback_response(message: str) -> dict:
    return {
        "response_text": message,
        "intent": "general_query",
        "data_required": "none",
        "emotion": "friendly",
        "extracted": {}
    }


HUMANIZER_PROMPT = """You are a warm, friendly IRCTC railway assistant for Indian Railways.

You will be given structured railway data. Your job is to convert it into a natural, 
conversational reply — like a helpful friend explaining it, not a robot reading data.

Rules:
1. Be warm, friendly and helpful. Use simple English.
2. Keep it concise — 3 to 5 sentences max.
3. Highlight the most important information first.
4. Add helpful context where relevant.
5. End with a helpful offer like "Anything else I can help you with? 😊"
6. Use 1-2 emojis naturally.
7. NEVER make up data.
8. Output ONLY the reply text.
"""


def humanize_response(raw_data_text: str, intent: str, context: str = "") -> str:
    intent_context = {
        "pnr_status": "The user asked about their PNR / ticket status.",
        "train_status": "The user asked about live train running status.",
        "seat_availability": "The user asked about seat availability for booking.",
    }

    user_prompt = (
        f"{intent_context.get(intent, 'The user asked a railway question.')}\n\n"
        f"Here is the railway data:\n\n"
        f"{raw_data_text}\n\n"
        f"{'Additional context: ' + context if context else ''}\n\n"
        f"Now write a warm, friendly reply based on this data."
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": user_prompt,
        "system": HUMANIZER_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        for attempt in range(2):
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(OLLAMA_URL, json=payload)
                    response.raise_for_status()
                break
            except httpx.TimeoutException:
                if attempt == 1:
                    return raw_data_text
                continue

        result = response.json()
        reply = result.get("response", "").strip()

        reply = re.sub(r"```.*?```", "", reply, flags=re.DOTALL).strip()
        reply = re.sub(r"^\{.*?\}$", "", reply, flags=re.DOTALL).strip()

        if not reply or len(reply) < 20:
            return raw_data_text

        return reply

    except Exception:
        return raw_data_text
