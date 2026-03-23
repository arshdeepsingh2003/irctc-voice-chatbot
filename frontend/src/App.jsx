import { useState } from "react";

const API_URL = "http://localhost:8000";

function App() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setResponse({ response_text: "Error connecting to backend!", intent: "error", emotion: "sad" });
    }

    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "60px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h1>🚂 IRCTC Voice Chatbot</h1>
      <p style={{ color: "#666" }}>Phase 1 — Basic connection test</p>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type a message..."
          style={{ flex: 1, padding: "10px 14px", fontSize: 16, borderRadius: 8, border: "1px solid #ccc" }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{ padding: "10px 20px", fontSize: 16, borderRadius: 8, background: "#2563eb", color: "#fff", border: "none", cursor: "pointer" }}
        >
          {loading ? "..." : "Send"}
        </button>
      </div>

      {response && (
        <div style={{ marginTop: 24, padding: 16, background: "#f1f5f9", borderRadius: 10 }}>
          <p><strong>Response:</strong> {response.response_text}</p>
          <p><strong>Intent:</strong> {response.intent}</p>
          <p><strong>Emotion:</strong> {response.emotion}</p>
        </div>
      )}
    </div>
  );
}

export default App;