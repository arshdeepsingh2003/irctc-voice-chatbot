import React, { useState } from "react";
import axios from "axios";

const VoiceBot = () => {
  const [messages, setMessages] = useState([]);
  const [listening, setListening] = useState(false);

  const startListening = () => {
    try {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

      if (!SpeechRecognition) {
        alert("Speech Recognition not supported. Please use Chrome.");
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.lang = "en-IN";

      setListening(true);
      recognition.start();

      recognition.onresult = async (event) => {
        const text = event.results[0][0].transcript;

        setMessages((prev) => [...prev, { type: "user", text }]);

        try {
          const res = await axios.post("http://localhost:8000/chat", {
            user_text: text,
          });

          const botText = res.data.response_text;

          setMessages((prev) => [...prev, { type: "bot", text: botText }]);

          const audio = new Audio(
            `http://localhost:8000${res.data.audio_url}`
          );
          audio.play();
        } catch (error) {
          console.error("API Error:", error);
        }

        setListening(false);
      };

      recognition.onerror = (e) => {
        console.error("Speech error:", e);
        setListening(false);
      };

      recognition.onend = () => {
        setListening(false);
      };

    } catch (err) {
      console.error("Crash error:", err);
    }
  };

  return (
    <div className="container">
      <h1>🚆 IRCTC Voice Assistant</h1>

      <button onClick={startListening}>
        {listening ? "Listening..." : "🎤 Speak"}
      </button>

      <div>
        {messages.map((msg, index) => (
          <div key={index}>
            <b>{msg.type === "user" ? "You: " : "Bot: "}</b>
            {msg.text}
          </div>
        ))}
      </div>
    </div>
  );
};

export default VoiceBot;