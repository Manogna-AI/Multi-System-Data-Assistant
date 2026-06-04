export default function ToolTracePanel({ traces }) {
  return (
    <aside className="trace-panel">
      <h2>Tool trace</h2>
      {!traces.length && <p>No tools called yet.</p>}
      {traces.map((trace, index) => (
        <div className="trace-item" key={`${trace.server}-${trace.tool}-${index}`}>
          <strong>{trace.server}.{trace.tool}</strong>
          <span>{trace.status}</span>
          <pre>{JSON.stringify(trace.arguments, null, 2)}</pre>
        </div>
      ))}
    </aside>
  );
}
