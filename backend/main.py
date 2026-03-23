# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from intent_engine import detect_intent
from response_builder import build_response

app = FastAPI(title="IRCTC Voice Chatbot API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response_text: str
    intent: str
    data_required: str
    emotion: str

@app.get("/")
def root():
    return {"status": "IRCTC Chatbot API is running!", "version": "0.2.0"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Step 1: Validate input
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Step 2: Detect intent
    intent_result = detect_intent(request.message)

    # Step 3: Build response
    response = build_response(intent_result, request.message)

    return ChatResponse(**response)

@app.get("/health")
def health():
    return {"status": "ok"}