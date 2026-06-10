/**
 * App — Root application component with 3-column layout.
 *
 * Layout:
 *   ┌────────────────────────────────────────────────────────────┐
 *   │                         Header                             │
 *   ├──────────┬────────────────────────────┬───────────────────┤
 *   │  Left    │        Chat (largest)       │   Tool Trace     │
 *   │  Sidebar │   Messages + Composer       │   Panel          │
 *   │          │                             │                   │
 *   │ Agent    │   MessageBubble (markdown)  │  agent → tool    │
 *   │ New Chat │                             │  arguments       │
 *   │ History  │                             │  result          │
 *   │ FAQ      │                             │                   │
 *   └──────────┴────────────────────────────┴───────────────────┘
 *
 * Architecture Mapping:
 *   main.jsx → App → useChat() → chatApi → Backend
 *   App renders: Header, LeftSidebar, ChatWindow, ToolTracePanel,
 *                ActionConfirmation
 *
 * Data Flow:
 *   1. User types query (or clicks FAQ in LeftSidebar)
 *   2. ChatWindow/LeftSidebar calls onSubmit → useChat.submitQuery()
 *   3. useChat enforces guardrails (validation, rate limit)
 *   4. chatApi.sendChatQuery() → POST /chat/query → Backend
 *   5. Backend returns { answer, tool_trace, session_id, ... }
 *   6. useChat updates messages + toolTraces + saves to localStorage
 *   7. ChatWindow renders MessageBubble (markdown)
 *   8. ToolTracePanel renders tool call details
 *   9. LeftSidebar shows active agent + session history + FAQ
 */

import Header from "./components/Header.jsx";
import LeftSidebar from "./components/LeftSidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import ToolTracePanel from "./components/ToolTracePanel.jsx";
import ActionConfirmation from "./components/ActionConfirmation.jsx";
import useChat from "./hooks/useChat.js";

export default function App() {
  const {
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
  } = useChat();

  // Show action confirmation banner when action_agent is active
  const showActionBanner = agentName === "action_agent";

  return (
    <>
      <Header />
      <ActionConfirmation visible={showActionBanner} />
      <div className="layout">
        {/* ── Left Panel: Session + History + FAQ ────────────── */}
        <LeftSidebar
          agentName={agentName}
          sessionId={sessionId}
          sessions={sessions}
          onClearChat={clearChat}
          onSelectQuestion={submitQuery}
          onSwitchSession={switchSession}
          onDeleteSession={removeSession}
          loading={loading}
        />

        {/* ── Middle Panel: Chat (largest) ──────────────────── */}
        <ChatWindow
          messages={messages}
          onSubmit={submitQuery}
          loading={loading}
          error={error}
        />

        {/* ── Right Panel: Tool Trace ───────────────────────── */}
        <ToolTracePanel traces={toolTraces} />
      </div>
    </>
  );
}