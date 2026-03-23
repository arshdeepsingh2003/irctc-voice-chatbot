import { useState } from "react";
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
      text: "Namaste! 🙏 I'm your IRCTC assistant powered by AI. Ask me about PNR status, train running status, or seat availability!"
    }
  ]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setMessages(prev => [...prev, { from: "user", text: userText }]);
    setInput("");
    setLoading(true);

    const updatedHistory = [...history, { role: "user", content: userText }];

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, history: updatedHistory }),
      });

      if (!res.ok) throw new Error("Server error");
      const data = await res.json();

      setHistory([...updatedHistory, { role: "assistant", content: data.response_text }]);

      setMessages(prev => [
        ...prev,
        {
          from: "bot",
          text: data.response_text,
          intent: data.intent
        }
      ]);

    } catch {
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
    setMessages([{ from: "bot", text: "Chat cleared! How can I help you? 🚂" }]);
    setHistory([]);
  };

  return (
    <div className="container">

      {/* Header */}
      <div className="header">
        <div>
          <h1>🚂 IRCTC Voice Chatbot</h1>
          <p>Phase 3 — Ollama LLM</p>
        </div>
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
                {msg.intent.replace("_", " ")}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message bot loading">
            🤔 Thinking...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="input-area">
        <input
          className="input-box"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
          placeholder="Ask anything about your train..."
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={loading}
        >
          Send
        </button>
      </div>

      {/* Quick Tests */}
      <div className="quick-tests">
        <span className="quick-title">Try these:</span>

        {[
          "Check PNR 1234567890",
          "Where is Rajdhani Express?",
          "Any seats from Delhi to Mumbai?",
          "What classes does 12301 have?",
          "Hello!"
        ].map(q => (
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
  );
}