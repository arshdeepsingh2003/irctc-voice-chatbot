from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.llm.ollama import process_with_llm
from app.services.railway_api import handle_intent
from app.services.tts import text_to_speech

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve audio files
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

@app.post("/chat")
async def chat(data: dict):
    user_text = data.get("user_text")

    # Step 1: LLM
    llm_response = process_with_llm(user_text)
    intent = llm_response.get("intent")

    # Step 2: API call (mock)
    api_response = handle_intent(intent, user_text)

    # Step 3: Final response
    final_text = llm_response.get("response_text")

    if api_response:
        final_text += " " + api_response

    # Step 4: TTS
    audio_file = text_to_speech(final_text)

    return {
        "response_text": final_text,
        "intent": intent,
        "audio_url": f"/audio/{audio_file}"
    }