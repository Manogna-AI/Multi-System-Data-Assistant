/**
 * ChatHistory — Displays list of past chat sessions.
 *
 * Features:
 *   - Shows session title (first user message)
 *   - Shows agent name and relative timestamp
 *   - Active session is highlighted
 *   - Click to switch sessions
 *   - Delete button per session
 *   - Empty state when no history
 *
 * Architecture Mapping:
 *   ChatHistory → onSelectSession(id) → useChat.switchSession()
 *   ChatHistory → onDeleteSession(id) → useChat.removeSession()
 */

export default function ChatHistory({
  sessions,
  activeSessionId,
  onSelectSession,
  onDeleteSession,
  loading,
}) {
  if (!sessions || sessions.length === 0) {
    return (
      <div className="chat-history">
        <h3 className="sidebar-title">Chat History</h3>
        <p className="history-empty">No conversations yet.</p>
      </div>
    );
  }

  return (
    <div className="chat-history">
      <h3 className="sidebar-title">Chat History</h3>
      <div className="history-list">
        {sessions.map((session) => {
          const isActive = session.id === activeSessionId;
          return (
            <div
              key={session.id}
              className={`history-item ${isActive ? "active" : ""}`}
              onClick={() => !loading && onSelectSession(session.id)}
              title={session.title}
            >
              <div className="history-item-content">
                {isActive && <span className="active-dot">●</span>}

                <div className="history-item-text">
                  <span className="history-title">{session.title}</span>

                  <span className="history-meta">
                    {session.agentName && (
                      <span className="history-agent">{session.agentName}</span>
                    )}
                    <span className="history-time">
                      {formatRelativeTime(session.updatedAt)}
                    </span>
                  </span>
                </div>
              </div>

              <button
                className="history-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.id);
                }}
                title="Delete conversation"
                disabled={loading}
              >
                🗑️
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Formats a timestamp into a human-readable relative time.
 * e.g., "2 min ago", "1 hour ago", "Yesterday", "Jun 5"
 */
function formatRelativeTime(isoString) {
  if (!isoString) return "";

  const now = new Date();
  const then = new Date(isoString);
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin} min ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay === 1) return "Yesterday";
  if (diffDay < 7) return `${diffDay}d ago`;

  return then.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}