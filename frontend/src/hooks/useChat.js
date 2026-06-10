/**
 * useChat Hook — Manages chat state, multi-session history, and API communication.
 *
 * This hook encapsulates:
 *   - Message history (user + assistant) per session
 *   - Multi-session management (create, switch, delete, persist)
 *   - Session persistence via localStorage
 *   - Loading/error state
 *   - Guardrail enforcement (validation + rate limiting)
 *   - Tool trace collection from API responses
 *
 * Architecture Mapping:
 *   App.jsx → useChat() → chatApi.js → Backend
 *   useChat() → sessionStorage.js → localStorage (persistence)
 */

import { useState, useCallback, useEffect } from "react";
import { sendChatQuery } from "../api/chatApi";
import { validateQuery, checkRateLimit, checkMessageLimit } from "../utils/guardrails";
import {
  loadSessions,
  saveSession,
  deleteSession as removeStoredSession,
  getSession,
  generateTitle,
} from "../utils/sessionStorage";

export default function useChat() {
  const [messages, setMessages] = useState([]);
  const [toolTraces, setToolTraces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [agentName, setAgentName] = useState(null);
  const [sessions, setSessions] = useState([]);

  // ── Load Session History on Mount ────────────────────────────
  useEffect(() => {
    setSessions(loadSessions());
  }, []);

  // ── Persist Current Session When Messages Change ─────────────
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      saveSession({
        id: sessionId,
        title: generateTitle(messages),
        agentName: agentName,
        messages: messages,
        toolTraces: toolTraces,
      });
      // Refresh session list
      setSessions(loadSessions());
    }
  }, [messages, toolTraces, sessionId, agentName]);

  // ── Submit Query ─────────────────────────────────────────────
  const submitQuery = useCallback(
    async (query) => {
      // ── Guardrail 1: Input Validation ──────────────────────
      const validation = validateQuery(query);
      if (!validation.valid) {
        setError(validation.error);
        return;
      }

      // ── Guardrail 2: Rate Limiting ─────────────────────────
      const rateCheck = checkRateLimit();
      if (!rateCheck.allowed) {
        setError(`Please wait ${Math.ceil(rateCheck.waitMs / 1000)}s before sending again.`);
        return;
      }

      // ── Guardrail 3: Message Limit ─────────────────────────
      const limitCheck = checkMessageLimit(messages.length);
      if (!limitCheck.allowed) {
        setError(limitCheck.error);
        return;
      }

      // ── Add User Message ───────────────────────────────────
      const userMessage = { role: "user", content: query };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      try {
        // ── Call Backend API ──────────────────────────────────
        const data = await sendChatQuery(query, "default_user", sessionId);

        // ── Update Session ID (multi-turn context) ───────────
        if (data.session_id) {
          setSessionId(data.session_id);
        }

        // ── Update Agent Name ────────────────────────────────
        if (data.agent_name) {
          setAgentName(data.agent_name);
        }

        // ── Add Assistant Response ───────────────────────────
        const assistantMessage = {
          role: "assistant",
          content: data.answer || "No response from agent.",
          agentName: data.agent_name,
          eventsCount: data.events_count,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // ── Update Tool Traces ───────────────────────────────
        if (data.tool_trace && data.tool_trace.length > 0) {
          setToolTraces(data.tool_trace);
        }

        // ── Handle API-Level Errors ──────────────────────────
        if (data.error) {
          setError(`Agent error: ${data.error}`);
        }
      } catch (err) {
        // Show error ONLY in the banner — NOT as a chat message
        setError(err.message || "Failed to get response. Is the backend running?");
      } finally {
        setLoading(false);
      }
    },
    [sessionId, messages.length]
  );

  // ── Start New Chat ───────────────────────────────────────────
  const clearChat = useCallback(() => {
    setMessages([]);
    setToolTraces([]);
    setError(null);
    setSessionId(null);
    setAgentName(null);
  }, []);

  // ── Switch to Existing Session ───────────────────────────────
  const switchSession = useCallback(
    (targetSessionId) => {
      if (targetSessionId === sessionId) return;

      const session = getSession(targetSessionId);
      if (!session) return;

      setMessages(session.messages || []);
      setToolTraces(session.toolTraces || []);
      setSessionId(session.id);
      setAgentName(session.agentName || null);
      setError(null);
    },
    [sessionId]
  );

  // ── Delete a Session ─────────────────────────────────────────
  const removeSession = useCallback(
    (targetSessionId) => {
      removeStoredSession(targetSessionId);
      setSessions(loadSessions());

      // If deleting the active session, clear the chat
      if (targetSessionId === sessionId) {
        clearChat();
      }
    },
    [sessionId, clearChat]
  );

  return {
    messages,
    toolTraces,
    loading,
    error,
    sessionId,
    agentName,
    sessions,
    submitQuery,
    clearChat,
    switchSession,
    removeSession,
  };
}