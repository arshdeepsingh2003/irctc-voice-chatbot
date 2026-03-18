# LLM handling (intent + response)
import requests
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configs from .env
OLLAMA_URL = os.getenv("OLLAMA_URL")
APP_ENV = os.getenv("APP_ENV", "development")


def process_with_llm(user_text):
    """
    Sends user query to Ollama LLM and returns structured JSON response
    """

    if not user_text:
        return {
            "response_text": "I didn’t catch that. Could you please repeat?",
            "intent": "general_query",
            "data_required": None,
            "emotion": "polite"
        }

    prompt = f"""
You are a human-like IRCTC railway help desk assistant.

User query: {user_text}

Your responsibilities:

1. Detect intent:
   - train_status
   - pnr_status
   - seat_availability
   - general_query

2. Respond like a real human:
   - polite, friendly, conversational
   - always acknowledge the request first
   - do NOT sound robotic

3. If required information is missing:
   - ask politely for it

STRICT RULES:
- Do NOT give short answers
- Do NOT output anything except JSON

Return ONLY this format:
{{
  "response_text": "natural human-like response",
  "intent": "intent_name",
  "data_required": null,
  "emotion": "friendly"
}}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=30
        )

        response.raise_for_status()

        result = response.json().get("response", "")

        # ✅ Direct JSON parse
        try:
            return json.loads(result)

        except json.JSONDecodeError:
            # 🔥 Fallback extraction
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                return json.loads(match.group())

            raise ValueError("No valid JSON found")

    except Exception as e:
        if APP_ENV == "development":
            print("❌ LLM ERROR:", str(e))
            print("🔍 RAW OUTPUT:", result if 'result' in locals() else "No output")

        return {
            "response_text": "Sorry, I’m having trouble processing that right now. Please try again.",
            "intent": "general_query",
            "data_required": None,
            "emotion": "neutral"
        }