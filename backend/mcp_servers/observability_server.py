"""
🔵 Observability MCP Server — FastMCP with Streamable HTTP Transport.

Exposes system telemetry tools via MCP protocol:
  - get_logs(service_name, start_time, end_time) → list
  - get_metrics(service_name, metric_name, window) → dict
  - get_alerts(service_name) → list

Properties: Read-Only · Time Validated · Size Limited

Architecture Mapping:
  MCP TOOLS LAYER → 🔵 Observability Server
  Mounted into gateway.py for unified access.

References:
  - FastMCP Composition: https://fastmcp.wiki/en/servers/composition
  - FastMCP: https://gofastmcp.com
"""

from fastmcp import FastMCP

from app.config import get_settings
from app.data.mock_observability import (
    MOCK_ALERTS,
    MOCK_LOGS,
    MOCK_METRICS,
    in_range,
)
from app.utils.validators import (
    validate_service_name,
    validate_time_range,
    validate_window,
)

# ── FastMCP Server Instance (mounted by gateway.py) ──────────────

def create_mcp_server():
    if FastMCP is None:
        raise RuntimeError("FastMCP not installed")
    return FastMCP("observability-server")

mcp = create_mcp_server()


@mcp.tool()
def get_logs(service_name: str, start_time: str, end_time: str) -> list[dict]:
    """Retrieve service logs filtered by service name and time range.

    Args:
        service_name: Target service (must be in allowlist).
        start_time: ISO 8601 UTC start timestamp.
        end_time: ISO 8601 UTC end timestamp (max 24h window).

    Returns:
        List of structured log entries, limited to 50 results.
    """
    service = validate_service_name(service_name)
    start, end = validate_time_range(start_time, end_time)
    logs = [
        dict(log)
        for log in MOCK_LOGS
        if log["service_name"] == service and in_range(log["timestamp"], start, end)
    ]
    return logs[: get_settings().max_log_results]


@mcp.tool()
def get_metrics(service_name: str, metric_name: str, window: str) -> dict:
    """Retrieve performance metrics for a service over a specified window.

    Args:
        service_name: Target service (must be in allowlist).
        metric_name: Metric to retrieve (e.g., error_rate, latency_p95, throughput).
        window: Aggregation window (1h, 6h, 12h, or 24h).

    Returns:
        Dict with metric_name, window, value, unit, baseline, and service_name.
    """
    service = validate_service_name(service_name)
    win = validate_window(window)
    key = (service, metric_name, win)
    metric = MOCK_METRICS.get(key)
    if metric is None:
        return {
            "error": f"No metric '{metric_name}' for '{service}' in window '{win}'.",
            "available_metrics": sorted(
                {k[1] for k in MOCK_METRICS if k[0] == service}
            ),
        }
    return dict(metric)


@mcp.tool()
def get_alerts(service_name: str) -> list[dict]:
    """Retrieve active and recent alerts for a service.

    Args:
        service_name: Target service (must be in allowlist).

    Returns:
        List of alert dicts, limited to 25 results.
    """
    service = validate_service_name(service_name)
    return [
        dict(alert) for alert in MOCK_ALERTS if alert["service_name"] == service
    ][:25]


# ── Standalone Entry Point (optional — for running individually) ──
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8010, path="/mcp")