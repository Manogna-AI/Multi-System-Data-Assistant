/**
 * Chat API Client — Communicates with FastAPI backend.
 *
 * Architecture Mapping:
 *   Frontend → chatApi.js → POST /chat/query → FastAPI → ADK Runner → Agents → MCP Servers
 *
 * API Contract (matches backend schemas/chat.py):
 *   Request:  { query, user_id, session_id }
 *   Response: { answer, session_id, agent_name, events_count, tool_trace, error }
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error(
    "VITE_API_BASE_URL is not defined. Create a .env file in frontend/ with:\n" +
    "VITE_API_BASE_URL=http://localhost:8001"
  );
}

/**
 * Sends a chat query to the backend ADK agent pipeline.
 *
 * @param {string} query - User's natural language question
 * @param {string} userId - Unique user identifier for session management
 * @param {string|null} sessionId - Existing session ID for multi-turn context
 * @returns {Promise<object>} ChatQueryResponse from backend
 */
export async function sendChatQuery(query, userId = "default_user", sessionId = null) {
  const body = {
    query,
    user_id: userId,
  };

  // Include session_id only if we have one (multi-turn)
  if (sessionId) {
    body.session_id = sessionId;
  }

  const response = await fetch(`${API_BASE_URL}/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown API error" }));
    throw new Error(error.detail || error.error || `Request failed (${response.status})`);
  }

  return response.json();
}

/**
 * Fetches the list of MCP servers and their tools.
 * Used by Header component to show server status.
 */
export async function fetchMCPServers() {
  const response = await fetch(`${API_BASE_URL}/mcp/servers`);
  if (!response.ok) return null;
  return response.json();
}

/**
 * Health check — verifies backend is reachable.
 */
export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) return { status: "unhealthy" };
    return response.json();
  } catch {
    return { status: "unreachable" };
  }
}