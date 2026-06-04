export default function ActionConfirmation({ pendingQuery, status, onConfirm }) {
  if (!pendingQuery && !status) return null;
  return (
    <div className="confirmation">
      <h3>Action confirmation</h3>
      {pendingQuery ? (
        <>
          <p>This action requires explicit confirmation before confirm=True is sent to the MCP Action Server.</p>
          <button onClick={onConfirm}>Confirm safe action</button>
        </>
      ) : null}
      {status ? <p>Status: <strong>{status.status || 'pending'}</strong> {status.message ? `— ${status.message}` : ''}</p> : null}
    </div>
  );
}
