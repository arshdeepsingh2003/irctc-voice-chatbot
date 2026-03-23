from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="IRCTC Voice Chatbot API")

# This allows your React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React runs here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This defines what a chat message looks like
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response_text: str
    intent: str
    data_required: str
    emotion: str

@app.get("/")
def root():
    return {"status": "IRCTC Chatbot API is running!"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Phase 1: Just echoes back for now — real logic comes in Phase 2+
    return ChatResponse(
        response_text=f"You said: {request.message}",
        intent="general_query",
        data_required="none",
        emotion="friendly"
    )