import { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL;

const intentColors = {
  pnr_status: "#f59e0b",
  train_status: "#3b82f6",
  seat_availability: "#10b981",
  general_query: "#6b7280",
  error: "#ef4444",
};

export default function App() {

  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "Namaste! I'm your IRCTC assistant. Ask me about PNR status, train running status, or seat availability!"
    }
  ]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [pendingIntent, setPendingIntent] = useState(null);
  const [pendingData, setPendingData] = useState({});

  // 🎤 Listening state
  const [listening, setListening] = useState(false);

  // 🔊 TTS state
  const [speaking, setSpeaking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const synthRef = useRef(window.speechSynthesis);

  // 🎤 Speech Recognition
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.log("Speech Recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN";

    recognitionRef.current = recognition;

    recognition.onstart = () => setListening(true);

    recognition.onresult = (event) => {
      let transcript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      setInput(transcript);

      if (event.results[event.results.length - 1].isFinal) {
        recognition.finalText = transcript;
      }
    };

    recognition.onend = () => {
      setListening(false);

      if (recognition.finalText?.trim()) {
        const finalText = recognition.finalText;
        recognition.finalText = "";
        setTimeout(() => sendMessage(finalText), 200);
      }
    };

  }, []);

  const startListening = () => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    recognition.start();
  };

  // 🔊 Speak function
  const speak = (text) => {
    if (!ttsEnabled || !synthRef.current) return;

    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);

    synthRef.current.speak(utterance);
  };

  const stopSpeaking = () => {
    synthRef.current.cancel();
    setSpeaking(false);
  };

  // Auto scroll
  const bottomRef = useRef(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Send Message ──
  const sendMessage = async (customText) => {
    const userText = customText || input.trim();
    if (!userText || loading) return;

    setMessages(prev => [...prev, { from: "user", text: userText }]);
    setInput("");
    setLoading(true);

    const updatedHistory = [
      ...history,
      { role: "user", content: userText }
    ];

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userText,
          history: updatedHistory,
          pending_intent: pendingIntent,
          pending_data: pendingData
        }),
      });

      if (!res.ok) throw new Error("Server error");

      const data = await res.json();

      setPendingIntent(data.pending_intent || null);
      setPendingData(data.pending_data || {});

      setHistory(prev => [
        ...prev,
        { role: "user", content: userText },
        { role: "assistant", content: data.response_text }
      ]);

      const botMsg = {
        from: "bot",
        text: data.response_text,
        intent: data.intent
      };

      setMessages(prev => [...prev, botMsg]);

      // 🔊 Speak response
      speak(data.response_text);

    } catch (err) {
      console.error(err);

      setMessages(prev => [
        ...prev,
        {
          from: "bot",
          text: "⚠️ Cannot connect to backend. Make sure backend & Ollama are running.",
          intent: "error"
        }
      ]);
    }

    setLoading(false);
  };

  const clearChat = () => {
    stopSpeaking();
    setMessages([
      { from: "bot", text: "Chat cleared! How can I help you? 🚂" }
    ]);
    setHistory([]);
    setPendingIntent(null);
    setPendingData({});
  };

  return (
    <div className="container">

      <div className="header">
        <div>
          <h1>🚂 IRCTC Voice Chatbot</h1>
          <p>Voice Enabled Chat</p>
        </div>

        {pendingIntent && (
          <div className="pending-badge">
            Collecting: {pendingIntent.replace("_", " ")}
          </div>
        )}

        <button
          className="clear-btn"
          onClick={() => {
            setTtsEnabled(prev => !prev);
            stopSpeaking();
          }}
        >
          {ttsEnabled ? "🔊 Voice ON" : "🔇 Voice OFF"}
        </button>

        <button className="clear-btn" onClick={clearChat}>
          Clear Chat
        </button>
      </div>



      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.from}`}>
            {msg.text}

            {msg.from === "bot" && ttsEnabled && (
              <button
                className="replay-icon"
                onClick={() => speak(msg.text)}
              >
                🔊
              </button>
            )}

            {msg.intent && (
              <div
                className="intent"
                style={{ color: intentColors[msg.intent] || "#888" }}
              >
                {msg.intent.replace(/_/g, " ")}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message bot loading">
            🤔 Thinking...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <input
          className="input-box"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask anything about your train..."
        />

        <button
          className={`mic-btn ${listening ? "mic-active" : ""}`}
          onClick={startListening}
        >
          {listening ? "🎙️ Listening..." : "🎙️"}
        </button>

        <button
          className="send-btn"
          onClick={() => sendMessage()}
          disabled={loading}
        >
          Send
        </button>
      </div>

      
    </div>
  );
}
