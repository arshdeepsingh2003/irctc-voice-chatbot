# main.py - v0.9 (MEMORY ENABLED)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from intent_engine import detect_intent
from intent_router import route_intent
from memory_store import update_memory, build_memory_context, clear_memory  # ✅ NEW

app = FastAPI(title="IRCTC Voice Chatbot API", version="0.9")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ──

class ConversationTurn(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ConversationTurn]] = []
    pending_intent: Optional[str] = None
    pending_data: Optional[dict] = {}
    session_id: Optional[str] = "default"   # ✅ NEW

class ChatResponse(BaseModel):
    response_text: str
    intent: str
    data_required: str
    emotion: str
    pending_intent: Optional[str] = None
    pending_data: Optional[dict] = {}

# ── Helper ──

def merge_extracted(base: dict, new: dict) -> dict:
    result = dict(base)
    for key, value in new.items():
        if value is not None and value != "" and value != "null":
            result[key] = value
    return result

# ── Routes ──

@app.get("/")
def root():
    return {"status": "IRCTC Chatbot API running", "version": "0.9"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # ── Validation ──
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id or "default"  # ✅ NEW

    history = [{"role": t.role, "content": t.content} for t in request.history]

    pending_intent = request.pending_intent or None
    pending_data = request.pending_data or {}

    print("\n=== INCOMING ===")
    print("message        :", request.message)
    print("pending_intent :", pending_intent)
    print("pending_data   :", pending_data)

    # ── Build memory context ──
    memory_context = build_memory_context(session_id)  # ✅ NEW

    # ── Step 1: Detect intent ──
    intent_result = detect_intent(request.message, history, memory_context)  # ✅ UPDATED

    # ── Update memory ──
    update_memory(session_id, intent_result, request.message)  # ✅ NEW

    ollama_intent = intent_result.get("intent", "general_query")
    ollama_extracted = intent_result.get("extracted", {})

    print("=== OLLAMA RESULT ===")
    print("intent    :", ollama_intent)
    print("extracted :", ollama_extracted)

    # 🔥 FIX 1 — Smart fallback
    if pending_intent and ollama_intent == "general_query":
        ollama_intent = pending_intent

    # ── Step 2: Context continuation ──
    if pending_intent:
        final_intent = pending_intent

        final_extracted = merge_extracted(pending_data, ollama_extracted)

        intent_result["intent"] = final_intent
        intent_result["extracted"] = final_extracted

        print("=== AFTER MERGE ===")
        print("final_intent    :", final_intent)
        print("final_extracted :", final_extracted)

    # ── Step 3: Route ──
    response = route_intent(intent_result, memory_context)  # ✅ UPDATED

    status = response.get("status", "")

    print("=== HANDLER RESPONSE ===")
    print("status        :", status)
    print("data_required :", response.get("data_required"))

    # ── Step 4: Decide next state ──

    if status == "missing_data":
        next_pending_intent = intent_result.get("intent")
        next_pending_data = intent_result.get("extracted", {})

    elif status in ["success", "api_error"]:
        next_pending_intent = None
        next_pending_data = {}

    elif status == "invalid_data":
        next_pending_intent = intent_result.get("intent")
        next_pending_data = intent_result.get("extracted", {})

    else:
        next_pending_intent = None
        next_pending_data = {}

    print("=== NEXT PENDING ===")
    print("next_pending_intent :", next_pending_intent)
    print("next_pending_data   :", next_pending_data)

    return ChatResponse(
        response_text=response["response_text"],
        intent=response["intent"],
        data_required=response["data_required"],
        emotion=response["emotion"],
        pending_intent=next_pending_intent,
        pending_data=next_pending_data
    )

# ✅ NEW ENDPOINT
@app.delete("/memory/{session_id}")
def clear_session_memory(session_id: str):
    clear_memory(session_id)
    return {"status": "memory cleared", "session_id": session_id}