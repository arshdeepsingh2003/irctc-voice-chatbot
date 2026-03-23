import httpx
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL_NAME = os.getenv("OLLAMA_MODEL")


# 🔥 FINAL SYSTEM PROMPT (STRICT + SAFE)
SYSTEM_PROMPT = """You are an IRCTC railway assistant. You MUST respond ONLY in valid JSON.

CRITICAL RULES — follow exactly:
1. Output ONLY raw JSON. No explanation. No markdown. No extra text.
2. A 10-digit number after "PNR" is ALWAYS a valid PNR number. Never question it.
3. A 4-5 digit number after "train" is ALWAYS a valid train number.
4. Never ask the user to re-enter data they already gave.
5. Only extract values explicitly present in the CURRENT user message.
6. NEVER reuse or infer values from previous conversation history.
7. If a value is not present in the current message, set it to null.
8. Do NOT guess missing fields like date, class, or stations.

Intent rules (follow strictly — do not mix these up):
- User mentions PNR number OR asks about ticket/booking status → intent = "pnr_status"
- User asks where a train IS, live location, running status, "where is train XXXXX" → intent = "train_status"
- User asks about seat availability, booking seats → intent = "seat_availability"
- Greetings, general questions, help → intent = "general_query"

IMPORTANT:
- "Where is train 12301" is ALWAYS train_status. Never pnr_status.
- Only set intent = pnr_status when the user explicitly mentions PNR.

JSON format (always return this exact structure):
{
  "response_text": "your reply here",
  "intent": "pnr_status | train_status | seat_availability | general_query",
  "data_required": "pnr_number | train_number | none",
  "emotion": "friendly",
  "extracted": {
    "pnr_number": "10-digit number or null",
    "train_number": "4-5 digit number or null",
    "date": "date string or null",
    "class": "SL/3A/2A/1A or null",
    "from_station": "station name or null",
    "to_station": "station name or null"
  }
}"""


# 🔥 ANTI-HALLUCINATION CLEANER (MOST IMPORTANT)
def clean_extracted_fields(extracted: dict, user_message: str) -> dict:
    """
    Keeps ONLY values present in current user message.
    Removes hallucinated values from history.
    """
    text = user_message.lower()
    cleaned = {}

    # ✅ PNR (strict 10 digits)
    pnr_match = re.findall(r"\b\d{10}\b", user_message)
    cleaned["pnr_number"] = pnr_match[0] if pnr_match else None

    # ✅ Train number (4–5 digits ONLY)
    train_match = re.findall(r"\b\d{4,5}\b", user_message)
    cleaned["train_number"] = train_match[0] if train_match else None

    # ✅ Date (only if explicitly mentioned)
    if any(word in text for word in ["today", "tomorrow"]):
        cleaned["date"] = extracted.get("date")
    else:
        cleaned["date"] = None

    # ✅ Class detection (only if present)
    classes = ["sl", "3a", "2a", "1a"]
    found_class = next((c.upper() for c in classes if c in text), None)
    cleaned["class"] = found_class

    # ✅ Stations (only if explicitly present)
    cleaned["from_station"] = extracted.get("from_station") if "from" in text else None
    cleaned["to_station"] = extracted.get("to_station") if "to" in text else None

    return cleaned


def ask_ollama(user_message: str, conversation_history: list = None) -> dict:
    """
    Sends user message to Ollama and returns parsed + cleaned response.
    """

    # 🔹 Limit history (prevents context leakage)
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
            "temperature": 0.2,  # 🔥 low = stable output
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

        # 🚨 FINAL SAFETY LAYER
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
    """
    Extract JSON safely from model output.
    """
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
    """
    Safe fallback response.
    """
    return {
        "response_text": message,
        "intent": "general_query",
        "data_required": "none",
        "emotion": "friendly",
        "extracted": {}
    }