import React, { useState } from "react";
import axios from "axios";
import ChatMessage from "./ChatMessage";

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

        // Add user message
        setMessages((prev) => [...prev, { type: "user", text }]);

        try {
          // Optional loading message
          setMessages((prev) => [
            ...prev,
            { type: "bot", text: "Checking..." },
          ]);

          const res = await axios.post("http://localhost:8000/chat", {
            user_text: text,
          });

          const botText = res.data.response_text;

          // Replace last "Checking..." message
          setMessages((prev) => {
            const updated = [...prev];
            updated.pop();
            return [...updated, { type: "bot", text: botText }];
          });

          // 🔊 Play audio
          const audio = new Audio(
            `http://localhost:8000${res.data.audio_url}`
          );
          audio.play();

        } catch (error) {
          console.error("API Error:", error);
          setMessages((prev) => [
            ...prev,
            { type: "bot", text: "Something went wrong. Please try again." },
          ]);
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

      <button className="mic-btn" onClick={startListening}>
        {listening ? "🎙️ Listening..." : "🎤 Speak"}
      </button>

      <div className="chat-box">
        {messages.map((msg, index) => (
          <ChatMessage key={index} type={msg.type} text={msg.text} />
        ))}
      </div>
    </div>
  );
};

export default VoiceBot;