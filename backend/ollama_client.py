
import httpx
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL_NAME = os.getenv("OLLAMA_MODEL")


SYSTEM_PROMPT = """You are an IRCTC railway assistant. You MUST respond ONLY in valid JSON.

CRITICAL RULES — follow exactly:
1. Output ONLY raw JSON. No explanation. No markdown. No extra text.
2. A 10-digit number after "PNR" is ALWAYS a valid PNR number. Never question it.
3. A 4-5 digit number after "train" is ALWAYS a valid train number.
4. Never ask the user to re-enter data they already gave.

Intent rules:
- User mentions PNR or ticket number → intent = "pnr_status"
- User asks where a train is / running status → intent = "train_status"
- User asks about seats / booking / availability → intent = "seat_availability"
- Anything else → intent = "general_query"

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


def ask_ollama(user_message: str, conversation_history: list = None) -> dict:
    """
    Sends user message to Ollama and returns parsed JSON response.
    conversation_history is a list of previous messages for context.
    """

    # Build the full prompt with conversation history for context
    history_text = ""
    if conversation_history:
        for turn in conversation_history[-4:]:  # last 4 turns only
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
            "temperature": 0.3,
            "top_p": 0.9
        }
    }

    try:
        # Increased timeout to 120 seconds, with retry
        for attempt in range(2):  # try twice
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(OLLAMA_URL, json=payload)
                    response.raise_for_status()
                break  # success, exit retry loop
            except httpx.TimeoutException:
                if attempt == 1:
                    return fallback_response("Ollama is taking too long. Try a smaller model like llama3.2:1b")
                continue  # retry once

        result = response.json()
        raw_text = result.get("response", "")

        # Parse the JSON response from Ollama
        parsed = parse_ollama_response(raw_text)
        return parsed

    except httpx.ConnectError:
        return fallback_response("Ollama is not running. Please start it with: ollama serve")
    except Exception as e:
        return fallback_response(f"Something went wrong: {str(e)}")


def parse_ollama_response(raw_text: str) -> dict:
    """
    Tries to extract valid JSON from Ollama's response.
    LLMs sometimes wrap JSON in markdown — this handles that.
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
        return fallback_response("I had trouble understanding that. Could you rephrase?")


def fallback_response(message: str) -> dict:
    """Returns a safe fallback response when Ollama fails."""
    return {
        "response_text": message,
        "intent": "general_query",
        "data_required": "none",
        "emotion": "friendly",
        "extracted": {}
    }