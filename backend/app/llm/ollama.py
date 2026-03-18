import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"

def process_with_llm(user_text):

    prompt = f"""
You are a friendly IRCTC railway assistant.

User: {user_text}

Detect intent:
- train_status
- pnr_status
- seat_availability
- general_query

Respond naturally.

STRICT RULE:
Return ONLY valid JSON. No extra text.

Format:
{{
"response_text": "...",
"intent": "...",
"data_required": null,
"emotion": "friendly"
}}
"""

    response = requests.post(OLLAMA_URL, json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    })

    raw_output = response.json()["response"]

    # 🔥 Extract JSON using regex
    try:
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            clean_json = json_match.group()
            return json.loads(clean_json)
    except Exception as e:
        print("Parsing error:", e)

    # fallback
    return {
        "response_text": "Sorry, I couldn't understand that. Could you please repeat?",
        "intent": "general_query"
    }