/**
 * MessageBubble — Renders a single chat message with Markdown support.
 *
 * User messages: plain text, blue bubble.
 * Assistant messages: full Markdown rendering (tables, code, lists, bold).
 *
 * Uses react-markdown with remark-gfm for GitHub Flavored Markdown
 * (tables, strikethrough, task lists).
 *
 * Architecture Mapping:
 *   Backend ChatQueryResponse.answer → MessageBubble → react-markdown → rendered HTML
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message ${isUser ? "user" : "assistant"}`}>
      {/* Agent badge for assistant messages */}
      {!isUser && message.agentName && (
        <div className="agent-badge">
          🤖 {message.agentName}
          {message.eventsCount > 0 && (
            <span className="events-count">{message.eventsCount} events</span>
          )}
        </div>
      )}

      {/* User messages: plain text | Assistant messages: Markdown */}
      {isUser ? (
        <span>{message.content}</span>
      ) : (
        <div className="markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}