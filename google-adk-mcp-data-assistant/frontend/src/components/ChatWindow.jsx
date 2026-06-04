import { useState } from 'react';
import MessageBubble from './MessageBubble.jsx';

export default function ChatWindow({ messages, onSubmit, loading, error }) {
  const [query, setQuery] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    if (!query.trim() || loading) return;
    onSubmit(query.trim());
    setQuery('');
  }

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map((message, index) => <MessageBubble key={`${message.role}-${index}`} message={message} />)}
        {loading && <div className="loading">Thinking through MCP tools...</div>}
        {error && <div className="error">{error}</div>}
      </div>
      <form className="composer" onSubmit={handleSubmit}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Why did revenue drop yesterday?" />
        <button type="submit" disabled={loading}>Send</button>
      </form>
    </div>
  );
}
