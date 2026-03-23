# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from intent_engine import detect_intent
from response_builder import build_response

app = FastAPI(title="IRCTC Voice Chatbot API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Models ----

class ConversationTurn(BaseModel):
    role: str     # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ConversationTurn]] = []   # conversation so far

class ChatResponse(BaseModel):
    response_text: str
    intent: str
    data_required: str
    emotion: str

# ---- Routes ----

@app.get("/")
def root():
    return {"status": "IRCTC Chatbot API is running!", "version": "0.3.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Convert history to plain dicts for ollama_client
    history = [{"role": t.role, "content": t.content} for t in request.history]

    # Detect intent using Ollama
    intent_result = detect_intent(request.message, history)

    # Build final response
    # If Ollama already gave us a response_text, use it directly
    if intent_result.get("response_text") and not intent_result.get("missing"):
        return ChatResponse(
            response_text=intent_result["response_text"],
            intent=intent_result["intent"],
            data_required=intent_result.get("data_required", "none"),
            emotion=intent_result.get("emotion", "friendly")
        )

    # Otherwise use response_builder for missing-info prompts
    response = build_response(intent_result, request.message)
    return ChatResponse(**response)