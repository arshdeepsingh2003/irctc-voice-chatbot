# 🚆 IRCTC Voice Chatbot

An AI-powered voice-based railway assistant that allows users to speak queries and receive spoken responses in real-time.

## 🎯 Features

- 🎤 Speech-to-Text (STT)
- 🧠 LLM-powered responses (Ollama)
- 🚆 Real-time train data (API)
- 🔊 Text-to-Speech (TTS)
- 💬 Human-like conversation

## 🏗️ Tech Stack

- Frontend: React
- Backend: FastAPI (Python)
- LLM: Ollama (LLaMA3)
- STT: Web Speech API
- TTS: gTTS / ElevenLabs

## ⚙️ Setup Instructions

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload