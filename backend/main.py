# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from intent_engine import detect_intent
from intent_router import route_intent

app = FastAPI(title="IRCTC Voice Chatbot API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Models ----

class ConversationTurn(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ConversationTurn]] = []

class ChatResponse(BaseModel):
    response_text: str
    intent: str
    data_required: str
    emotion: str

# ---- Routes ----

@app.get("/")
def root():
    return {"status": "IRCTC Chatbot API is running!", "version": "0.4.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Validate
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Step 1: Convert history to plain dicts
    history = [{"role": t.role, "content": t.content} for t in request.history]

    # Step 2: Detect intent using Ollama
    intent_result = detect_intent(request.message, history)

    # Step 3: Route to correct handler
    response = route_intent(intent_result)

    # Step 4: Return clean response
    return ChatResponse(
        response_text=response["response_text"],
        intent=response["intent"],
        data_required=response["data_required"],
        emotion=response["emotion"]
    )

