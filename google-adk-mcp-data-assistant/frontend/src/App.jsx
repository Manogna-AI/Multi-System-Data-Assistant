import { useState } from 'react';
import { sendChatQuery } from './api/chatApi.js';
import Header from './components/Header.jsx';
import ChatWindow from './components/ChatWindow.jsx';
import ToolTracePanel from './components/ToolTracePanel.jsx';
import ActionConfirmation from './components/ActionConfirmation.jsx';

export default function App() {
  const [messages, setMessages] = useState([{ role: 'assistant', content: 'Ask about revenue, customer impact, logs, metrics, alerts, or safe actions.' }]);
  const [lastTrace, setLastTrace] = useState([]);
  const [pendingActionQuery, setPendingActionQuery] = useState('');
  const [actionStatus, setActionStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(query, confirmAction = false) {
    setLoading(true);
    setError('');
    setMessages((items) => [...items, { role: 'user', content: confirmAction ? `${query} (confirmed)` : query }]);
    try {
      const result = await sendChatQuery(query, confirmAction);
      setLastTrace(result.tool_trace || []);
      setActionStatus(result.action_confirmation || null);
      if (result.action_confirmation?.required && !confirmAction) {
        setPendingActionQuery(query);
      } else {
        setPendingActionQuery('');
      }
      setMessages((items) => [...items, { role: 'assistant', content: result.answer }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <Header />
      <main className="layout">
        <section className="chat-card">
          <ChatWindow messages={messages} onSubmit={(query) => submit(query, false)} loading={loading} error={error} />
          <ActionConfirmation pendingQuery={pendingActionQuery} status={actionStatus} onConfirm={() => submit(pendingActionQuery, true)} />
        </section>
        <ToolTracePanel traces={lastTrace} />
      </main>
    </div>
  );
}
