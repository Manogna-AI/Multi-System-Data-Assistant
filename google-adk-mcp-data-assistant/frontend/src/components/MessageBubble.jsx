export default function MessageBubble({ message }) {
  return <div className={`message ${message.role}`}>{message.content}</div>;
}
