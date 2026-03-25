import { useState, useRef, useCallback, useEffect } from "react";

// ── Browser support ──
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

export const isSpeechSupported = !!SpeechRecognition;
export const isSynthesisSupported = !!window.speechSynthesis;

export function useSpeech({ onFinalTranscript }) {
  // ── STT state ──
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [voiceStatus, setVoiceStatus] = useState("");

  // ── TTS state ──
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [ttsVoice, setTtsVoice] = useState(null);
  const [availableVoices, setAvailableVoices] = useState([]);

  // ── Refs ──
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // ════════════════════════════════════
  // Load voices
  // ════════════════════════════════════
  useEffect(() => {
    if (!isSynthesisSupported) return;

    const loadVoices = () => {
      const voices = synthRef.current?.getVoices?.() || [];
      setAvailableVoices(voices);

      if (!voices.length) return;

      const preferred =
        voices.find((v) => v.lang === "en-IN") ||
        voices.find((v) => v.lang === "en-GB") ||
        voices.find((v) => v.lang.startsWith("en")) ||
        voices[0];

      setTtsVoice(preferred);
    };

    loadVoices();

    if (synthRef.current) {
      synthRef.current.onvoiceschanged = loadVoices;
    }

    return () => {
      if (synthRef.current) {
        synthRef.current.onvoiceschanged = null;
      }
    };
  }, []);

  // ════════════════════════════════════
  // TTS — Speak (ULTRA CLEAN FINAL)
  // ════════════════════════════════════
  const speak = useCallback(
    (text) => {
      if (!isSynthesisSupported || !ttsEnabled || !text) return;

      const synth = synthRef.current;
      if (!synth) return;

      // Stop any ongoing speech
      synth.cancel();

      // 🧠 EXTRA SAFETY: remove "Replay" from source text itself
      const safeText = text.replace(/\bReplay\b/gi, "");

      // 🔥 ULTRA CLEANING (handles ALL emojis + symbols)
      const cleanText = safeText
        // Remove ALL emoji + ZWJ + variation selectors
        .replace(
          /([\u2700-\u27BF]|[\uE000-\uF8FF]|[\uD83C-\uDBFF\uDC00-\uDFFF]+|[\uFE0F]|\u200D)/g,
          " "
        )

        // Remove anything non-ASCII (final safety)
        .replace(/[^\x00-\x7F]/g, " ")

        // Remove markdown / formatting
        .replace(/\*+/g, "")
        .replace(/#+/g, "")
        .replace(/_{1,}/g, "")
        .replace(/`+/g, "")

        // Convert symbols to natural speech
        .replace(/•/g, ",")
        .replace(/→/g, "to")
        .replace(/:/g, ",")

        // Convert line breaks to pauses
        .replace(/\n+/g, ". ")

        // Remove UI control symbols (play, replay, etc.)
        .replace(/[\u23E9-\u23EF\u25B6\u23F8\u23F9\u23FA\u21A9\u21AA]/g, " ")

        // Remove leftover special chars
        .replace(/[-_=+|<>{}[\]\\^~`@#$%^&*]/g, " ")

        // Clean punctuation & spacing
        .replace(/\.{2,}/g, ".")
        .replace(/,{2,}/g, ",")
        .replace(/\s{2,}/g, " ")
        .trim();

      // 🧪 Debug logs (VERY useful)
      console.log("RAW:", text);
      console.log("CLEAN:", cleanText);

      if (!cleanText || cleanText.length < 3) return;

      const utterance = new SpeechSynthesisUtterance(cleanText);

      utterance.voice = ttsVoice || null;
      utterance.rate = 0.92;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      utterance.lang = "en-IN";

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      synth.speak(utterance);
    },
    [ttsEnabled, ttsVoice]
  );

  const stopSpeaking = useCallback(() => {
    synthRef.current?.cancel();
    setIsSpeaking(false);
  }, []);

  // ════════════════════════════════════
  // STT — Listen
  // ════════════════════════════════════
  const startListening = useCallback(() => {
    if (!isSpeechSupported) {
      alert("Speech recognition not supported. Use Chrome/Edge.");
      return;
    }

    stopSpeaking();
    recognitionRef.current?.stop();

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setVoiceStatus("🎙️ Listening... speak now");
      setInterimText("");
    };

    recognition.onresult = (event) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += t;
        else interim += t;
      }

      if (interim) setInterimText(interim);

      if (final) {
        setInterimText("");
        onFinalTranscript(final.trim());
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimText("");
      setVoiceStatus("");
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      setInterimText("");

      const msgs = {
        "not-allowed": "❌ Mic permission denied",
        "no-speech": "🔇 No speech detected",
        network: "🌐 Network error",
        aborted: "",
      };

      const msg = msgs[event.error] || `Mic error: ${event.error}`;

      if (msg) {
        setVoiceStatus(msg);
        setTimeout(() => setVoiceStatus(""), 3000);
      }
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch {
      setVoiceStatus("Mic start failed");
      setTimeout(() => setVoiceStatus(""), 3000);
    }
  }, [onFinalTranscript, stopSpeaking]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
    setInterimText("");
    setVoiceStatus("");
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) stopListening();
    else startListening();
  }, [isListening, startListening, stopListening]);

  // Cleanup
  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
      synthRef.current?.cancel();
    };
  }, []);

  return {
    // STT
    isListening,
    interimText,
    voiceStatus,
    toggleListening,
    stopListening,

    // TTS
    isSpeaking,
    ttsEnabled,
    setTtsEnabled,
    ttsVoice,
    setTtsVoice,
    availableVoices,
    speak, 
    stopSpeaking,
  };
}