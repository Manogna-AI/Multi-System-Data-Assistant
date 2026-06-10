/**
 * LeftSidebar — Session info, chat history, and FAQ questions.
 *
 * Layout (top to bottom):
 *   1. Active agent badge + MCP-only badge
 *   2. New Chat button
 *   3. Chat History (scrollable list of past sessions)
 *   4. Divider
 *   5. FAQ Section (categorized clickable questions)
 *
 * Architecture Mapping:
 *   LeftSidebar → onSelectQuestion() → useChat.submitQuery() → Backend
 *   LeftSidebar → onClearChat() → useChat.clearChat()
 *   LeftSidebar → ChatHistory → onSwitchSession() → useChat.switchSession()
 *   LeftSidebar → ChatHistory → onDeleteSession() → useChat.removeSession()
 */

import ChatHistory from "./ChatHistory.jsx";
import FAQSection from "./FAQSection.jsx";

export default function LeftSidebar({
  agentName,
  sessionId,
  sessions,
  onClearChat,
  onSelectQuestion,
  onSwitchSession,
  onDeleteSession,
  loading,
}) {
  return (
    <div className="left-sidebar">
      {/* ── Session Info ─────────────────────────────────────── */}
      <div className="sidebar-section">
        <div className="sidebar-badges-row">
          {agentName ? (
            <div className="sidebar-badge active">
              🤖 {agentName}
            </div>
          ) : (
            <div className="sidebar-badge inactive">
              🤖 No agent active
            </div>
          )}
          <div className="sidebar-badge mcp-badge">
            🛡️ MCP-only
          </div>
        </div>

        <button
          className="sidebar-btn new-chat-btn"
          onClick={onClearChat}
          disabled={loading}
        >
          ✨ New Chat
        </button>
      </div>

      {/* ── Divider ──────────────────────────────────────────── */}
      <hr className="sidebar-divider" />

      {/* ── Chat History ─────────────────────────────────────── */}
      <div className="sidebar-section history-scroll">
        <ChatHistory
          sessions={sessions}
          activeSessionId={sessionId}
          onSelectSession={onSwitchSession}
          onDeleteSession={onDeleteSession}
          loading={loading}
        />
      </div>

      {/* ── Divider ──────────────────────────────────────────── */}
      <hr className="sidebar-divider" />

      {/* ── FAQ Section ──────────────────────────────────────── */}
      <div className="sidebar-section faq-scroll">
        <FAQSection onSelectQuestion={onSelectQuestion} disabled={loading} />
      </div>
    </div>
  );
}