/**
 * Session Storage Manager — Persists chat sessions to localStorage.
 *
 * Each session is stored as:
 * {
 *   id: "uuid",
 *   title: "First user message (truncated)",
 *   agentName: "observability_agent",
 *   messages: [...],
 *   toolTraces: [...],
 *   createdAt: ISO timestamp,
 *   updatedAt: ISO timestamp,
 * }
 *
 * Architecture Mapping:
 *   useChat hook → sessionStorage.js → localStorage
 *   On page refresh: sessionStorage.js → useChat hook (restores state)
 */

const STORAGE_KEY = "mcp_assistant_sessions";
const MAX_SESSIONS = 30;

/**
 * Load all sessions from localStorage.
 * Returns array sorted by updatedAt (newest first).
 */
export function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const sessions = JSON.parse(raw);
    return sessions.sort(
      (a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)
    );
  } catch {
    return [];
  }
}

/**
 * Save a session (create or update).
 * Automatically trims to MAX_SESSIONS.
 */
export function saveSession(session) {
  try {
    const sessions = loadSessions();
    const index = sessions.findIndex((s) => s.id === session.id);

    const updated = {
      ...session,
      updatedAt: new Date().toISOString(),
    };

    if (index >= 0) {
      sessions[index] = updated;
    } else {
      sessions.unshift({
        ...updated,
        createdAt: new Date().toISOString(),
      });
    }

    const trimmed = sessions.slice(0, MAX_SESSIONS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch (e) {
    console.warn("Failed to save session to localStorage:", e);
  }
}

/**
 * Delete a session by ID.
 */
export function deleteSession(sessionId) {
  try {
    const sessions = loadSessions();
    const filtered = sessions.filter((s) => s.id !== sessionId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  } catch (e) {
    console.warn("Failed to delete session:", e);
  }
}

/**
 * Load a specific session by ID.
 */
export function getSession(sessionId) {
  const sessions = loadSessions();
  return sessions.find((s) => s.id === sessionId) || null;
}

/**
 * Generate a title from the first user message.
 * Truncates to 50 characters.
 */
export function generateTitle(messages) {
  const firstUserMsg = messages.find((m) => m.role === "user");
  if (!firstUserMsg) return "New conversation";
  const text = firstUserMsg.content.trim();
  return text.length > 50 ? text.slice(0, 50) + "…" : text;
}