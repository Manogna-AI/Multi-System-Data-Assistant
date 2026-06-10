/**
 * ToolTracePanel — Displays MCP tool calls made during agent execution.
 *
 * Shows which agent called which tool, with what arguments,
 * and the result summary returned by the MCP server.
 *
 * Architecture Mapping:
 *   Backend ChatQueryResponse.tool_trace → ToolTracePanel → rendered trace items
 *
 * API Fields (from schemas/common.py ToolTraceItem):
 *   - agent: which ADK agent made the call
 *   - tool: which MCP tool was invoked
 *   - arguments: parameters passed to the tool
 *   - result_summary: truncated result from MCP server
 */

export default function ToolTracePanel({ traces }) {
  return (
    <div className="trace-panel">
      <h3>🔧 Tool Trace</h3>

      {!traces || traces.length === 0 ? (
        <p className="trace-empty">No tools called yet.</p>
      ) : (
        traces.map((trace, index) => (
          <div key={index} className="trace-item">
            <div className="trace-header">
              <span className="trace-agent">🤖 {trace.agent}</span>
              <span className="trace-arrow">→</span>
              <span className="trace-tool">{trace.tool}</span>
            </div>

            <div className="trace-args">
              <strong>Arguments:</strong>
              <pre>{JSON.stringify(trace.arguments, null, 2)}</pre>
            </div>

            <div className="trace-result">
              <strong>Result:</strong>
              <pre>{trace.result_summary}</pre>
            </div>
          </div>
        ))
      )}
    </div>
  );
}