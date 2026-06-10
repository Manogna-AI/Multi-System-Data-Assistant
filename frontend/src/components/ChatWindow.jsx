/**
 * ChatWindow — Main chat interface with input and messages.
 *
 * Features:
 *   - Message display with markdown rendering (MessageBubble)
 *   - Input composer with guardrails (length indicator, validation)
 *   - Loading state with animated dots
 *   - Error display banner
 *
 * NOTE: FAQ section is now in LeftSidebar, not here.
 *
 * Architecture Mapping:
 *   User types query → ChatWindow → useChat.submitQuery() → chatApi → Backend
 */

import { useState } from "react";
import MessageBubble from "./MessageBubble.jsx";
import { GUARDRAIL_LIMITS, APP_CONFIG } from "../utils/constants";

export default function ChatWindow({ messages, onSubmit, loading, error }) {
  const [query, setQuery] = useState("");

  const charCount = query.trim().length;
  const isOverLimit = charCount > GUARDRAIL_LIMITS.MAX_QUERY_LENGTH;
  const isEmpty = charCount === 0;

  function handleSubmit(event) {
    event.preventDefault();
    if (!query.trim() || loading || isOverLimit) return;
    onSubmit(query.trim());
    setQuery("");
  }

  return (
    <div className="chat-card chat-window">
      <div className="messages">
        {/* Welcome message when no messages */}
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2 className="welcome-heading">👋 Welcome</h2>
            <p className="welcome-text">{APP_CONFIG.PLACEHOLDER}</p>
            <p className="welcome-hint">
              Select a question from the left panel or type your own below.
            </p>
          </div>
        )}

        {/* Render message bubbles */}
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="message assistant loading-bubble">
            <div className="loading-dots">
              <span></span><span></span><span></span>
            </div>
            <span className="loading-text">Thinking through MCP tools...</span>
          </div>
        )}

        {/* Error display */}
        {error && <div className="error-message">{error}</div>}
      </div>

      {/* Input composer */}
      <form className="composer" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about revenue, logs, metrics, alerts, or actions..."
            maxLength={GUARDRAIL_LIMITS.MAX_QUERY_LENGTH + 10}
            disabled={loading}
          />
          {charCount > 0 && (
            <span className={`char-count ${isOverLimit ? "over-limit" : ""}`}>
              {charCount}/{GUARDRAIL_LIMITS.MAX_QUERY_LENGTH}
            </span>
          )}
        </div>
        <button type="submit" disabled={loading || isEmpty || isOverLimit}>
          {loading ? "⏳" : "Send"}
        </button>
      </form>
    </div>
  );
}