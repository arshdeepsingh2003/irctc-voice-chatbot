import React from "react";

const ChatMessage = ({ type, text }) => {
  return (
    <div className={`message ${type}`}>
      {text}
    </div>
  );
};

export default ChatMessage;