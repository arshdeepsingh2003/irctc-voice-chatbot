import { useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "Namaste! 🙏 I'm your IRCTC assistant. Ask me about PNR status, train running status, or seat availability!"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { from: "user", text: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });

      const data = await res.json();

      setMessages(prev => [
        ...prev,
        { from: "bot", text: data.response_text, intent: data.intent }
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          from: "bot",
          text: "⚠️ Cannot connect to backend. Is it running?",
          intent: "error"
        }
      ]);
    }

    setLoading(false);
  };

  return (
    <div className="container">

      {/* Header */}
      <div className="header">
        <h1>🚂 IRCTC Voice Chatbot</h1>
        <p>Phase 2 — Intent Detection</p>
      </div>

      {/* Chat Window */}
      <div className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.from}`}>
            {msg.text}

            {msg.intent && (
              <div className={`intent ${msg.intent}`}>
                Intent: {msg.intent}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message bot loading">
            Thinking...
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
          placeholder="Try: Check PNR 1234567890 or Where is train 12345"
        />

        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={loading}
        >
          Send
        </button>
      </div>

      {/* Quick Test Buttons */}
      <div className="quick-tests">
        <p className="quick-title">Quick tests:</p>

        {[
          "Check PNR 1234567890",
          "Where is train 12345",
          "Is seat available?",
          "Hello"
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

export default App;