import { useState, useRef, useEffect } from "react";
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

  // ── State ──
  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "Namaste! 🙏 I'm your IRCTC assistant powered by AI. Ask me about PNR status, train running status, or seat availability!"
    }
  ]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // ✅ Context state
  const [pendingIntent, setPendingIntent] = useState(null);
  const [pendingData, setPendingData] = useState({});

  // ✅ Auto scroll
  const bottomRef = useRef(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Send Message ──
  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userText = input.trim();

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

      // ✅ Save context
      setPendingIntent(data.pending_intent || null);
      setPendingData(data.pending_data || {});

      // ✅ Update history
      setHistory(prev => [
        ...prev,
        { role: "user", content: userText },
        { role: "assistant", content: data.response_text }
      ]);

      // ✅ Update UI
      setMessages(prev => [
        ...prev,
        {
          from: "bot",
          text: data.response_text,
          intent: data.intent
        }
      ]);

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

  // ── Clear Chat ──
  const clearChat = () => {
    setMessages([
      { from: "bot", text: "Chat cleared! How can I help you? 🚂" }
    ]);
    setHistory([]);

    // ✅ Reset context
    setPendingIntent(null);
    setPendingData({});
  };

  return (
    <div className="container">

      {/* Header */}
      <div className="header">
        <div>
          <h1>🚂 IRCTC Voice Chatbot</h1>
          <p>Phase 6 — Human-like responses</p>
        </div>

        {/* ✅ Pending intent badge */}
        {pendingIntent && (
          <div className="pending-badge">
            Collecting: {pendingIntent.replace("_", " ")}
          </div>
        )}

        <button className="clear-btn" onClick={clearChat}>
          Clear Chat
        </button>
      </div>

      {/* Chat Window */}
      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.from}`}>
            {msg.text}

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

        {/* ✅ Auto scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="input-area">
        <input
          className="input-box"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask anything about your train..."
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={loading}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>

      {/* Quick Tests */}
      <div className="quick-tests">
        <span className="quick-title">Try these:</span>

        {[
          "Check PNR 1234567890",
          "Where is train 12301",
          "I want to check seats",
          "Any seats from NDLS to BCT tomorrow in 3A?",
          "Hello!"
        ].map((q) => (
          <button
            key={q}
            className="quick-btn"
            onClick={() => setInput(q)}
          >
            {q}
          </button>
        ))}
      </div>

    </div>
  )
}