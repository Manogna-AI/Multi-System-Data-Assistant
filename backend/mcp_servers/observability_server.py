"""
🔵 Observability MCP Server — FastMCP with Streamable HTTP Transport.

Exposes system telemetry tools via MCP protocol:

  Existing Tools:
  - get_logs(service_name, start_time, end_time) → list
  - get_metrics(service_name, metric_name, window) → dict
  - get_alerts(service_name) → list

  New Tools:
  - get_service_health(service_name) → dict
  - list_services() → dict
  - search_logs(service_name, start_time, end_time, level, keyword) → dict
  - get_alert_summary(service_name) → dict

Properties: Read-Only · Time Validated · Size Limited · Aggregated

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
    MOCK_SERVICE_HEALTH,
    in_range,
)
from app.utils.validators import (
    validate_service_name,
    validate_time_range,
    validate_window,
)


# ── FastMCP Server Instance (mounted by gateway.py) ──────────────

def create_mcp_server():
    """
    Create and return the FastMCP server instance for the Observability MCP server.

    This factory function encapsulates MCP server creation so that server
    initialization is defined in one place and can be extended later if
    additional startup configuration is needed.

    Returns:
        FastMCP: The initialized MCP server instance for observability tools.

    Raises:
        RuntimeError: If the FastMCP library is unavailable in the current
            environment.
    """
    if FastMCP is None:
        raise RuntimeError("FastMCP not installed")
    return FastMCP("observability-server")


mcp = create_mcp_server()


# ═══════════════════════════════════════════════════════════════════════════
# EXISTING TOOLS (unchanged)
# ═══════════════════════════════════════════════════════════════════════════


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
        metric_name: Metric to retrieve (e.g., error_rate, latency_p95_ms, throughput).
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


# ═══════════════════════════════════════════════════════════════════════════
# NEW TOOLS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_service_health(service_name: str) -> dict:
    """Get comprehensive health summary for a single service.

    Supports queries like:
      - "Is payment-service healthy?"
      - "How many replicas does payment-service have?"
      - "When was payment-service last restarted?"
      - "Summarize payment-service health"
      - "What is the status of checkout-service?"
      - "Is maintenance mode on for payment-service?"

    Args:
        service_name: Target service (must be in allowlist).

    Returns:
        Dict with: service_name, status (healthy/degraded/down),
        current_replicas, max_replicas, uptime_hours, last_restart,
        active_alert_count, maintenance_mode.
        Returns error dict if service not found.
    """
    service = validate_service_name(service_name)
    health = MOCK_SERVICE_HEALTH.get(service)

    if health is None:
        return {
            "found": False,
            "service_name": service,
            "message": f"No health data available for '{service}'.",
            "available_services": sorted(MOCK_SERVICE_HEALTH.keys()),
        }

    return {
        "found": True,
        **dict(health),
    }


@mcp.tool()
def list_services() -> dict:
    """List all monitored services with current health status.

    Supports queries like:
      - "Show all services and their status"
      - "Which services are degraded?"
      - "What is the overall system health?"
      - "How many services are healthy?"
      - "Show all services"

    Returns:
        Dict with:
          - total_count: number of monitored services
          - services: list of service summaries
          - count_by_status: breakdown by health status
          - degraded_services: list of degraded/down service names
    """
    services = []
    count_by_status: dict[str, int] = {}
    degraded_services: list[str] = []

    for name, health in MOCK_SERVICE_HEALTH.items():
        service_summary = {
            "service_name": name,
            "status": health["status"],
            "current_replicas": health["current_replicas"],
            "active_alert_count": health["active_alert_count"],
            "uptime_hours": health["uptime_hours"],
        }
        services.append(service_summary)

        # Count by status
        st = health["status"]
        count_by_status[st] = count_by_status.get(st, 0) + 1

        # Track degraded/down services
        if st in ("degraded", "down"):
            degraded_services.append(name)

    return {
        "total_count": len(services),
        "services": services,
        "count_by_status": count_by_status,
        "degraded_services": degraded_services,
    }


@mcp.tool()
def search_logs(
    service_name: str,
    start_time: str,
    end_time: str,
    level: str = "",
    keyword: str = "",
) -> dict:
    """Search service logs with level and keyword filters.

    Enhanced version of get_logs with additional filtering capabilities.

    Supports queries like:
      - "Show ERROR logs for payment-service"
      - "Search logs containing timeout"
      - "Show WARN logs for checkout-service"
      - "How many errors happened today for payment-service?"
      - "Find logs with 503 in payment-service"
      - "Show DEBUG logs for troubleshooting"

    Args:
        service_name: Target service (must be in allowlist).
        start_time: ISO 8601 UTC start timestamp.
        end_time: ISO 8601 UTC end timestamp (max 24h window).
        level: Optional log level filter (ERROR, WARN, INFO, DEBUG).
               Case-insensitive. Empty string = all levels.
        keyword: Optional keyword to search in log messages.
                 Case-insensitive partial match. Empty string = no filter.

    Returns:
        Dict with:
          - total_count: number of matching logs
          - logs: list of matching log entries (limited to 50)
          - count_by_level: breakdown by log level
          - message: helper message
    """
    service = validate_service_name(service_name)
    start, end = validate_time_range(start_time, end_time)

    # Validate log level if provided
    allowed_levels = {"ERROR", "WARN", "INFO", "DEBUG"}
    normalized_level = ""
    if level:
        normalized_level = level.strip().upper()
        if normalized_level not in allowed_levels:
            return {
                "total_count": 0,
                "logs": [],
                "count_by_level": {},
                "message": f"Invalid log level '{level}'. Must be one of: {sorted(allowed_levels)}",
            }

    # Normalize keyword
    keyword_lower = keyword.strip().lower() if keyword else ""

    # Filter logs
    results = []
    for log in MOCK_LOGS:
        # Service filter
        if log["service_name"] != service:
            continue

        # Time range filter
        if not in_range(log["timestamp"], start, end):
            continue

        # Level filter
        if normalized_level and log.get("level", "") != normalized_level:
            continue

        # Keyword filter
        if keyword_lower and keyword_lower not in log.get("message", "").lower():
            continue

        results.append(dict(log))

    # Count by level
    count_by_level: dict[str, int] = {}
    for log in results:
        lvl = log.get("level", "UNKNOWN")
        count_by_level[lvl] = count_by_level.get(lvl, 0) + 1

    # Limit results
    max_results = get_settings().max_log_results
    limited_results = results[:max_results]

    # Build message
    filters_desc = [f"service={service}"]
    if normalized_level:
        filters_desc.append(f"level={normalized_level}")
    if keyword_lower:
        filters_desc.append(f"keyword='{keyword_lower}'")

    if results:
        message = f"Found {len(results)} log(s) matching filters: {', '.join(filters_desc)}."
    else:
        message = f"No logs found matching filters: {', '.join(filters_desc)}."

    return {
        "total_count": len(results),
        "logs": limited_results,
        "count_by_level": count_by_level,
        "message": message,
    }


@mcp.tool()
def get_alert_summary(service_name: str = "") -> dict:
    """Get alert statistics, optionally filtered by service.

    Supports queries like:
      - "Show all active alerts across all services"
      - "Show resolved alerts"
      - "Show critical alerts"
      - "How many alerts are active right now?"
      - "Which service has the most alerts?"
      - "Show alert summary for payment-service"

    Args:
        service_name: Optional service filter. Empty string = all services.
                      If provided, must be in allowlist.

    Returns:
        Dict with:
          - total_count: total number of alerts
          - active_count: number of open alerts
          - resolved_count: number of resolved alerts
          - alerts_by_severity: count breakdown by severity
          - alerts_by_service: count breakdown by service
          - alerts_by_status: count breakdown by status
          - active_alerts: list of open alert dicts
          - resolved_alerts: list of resolved alert dicts
          - most_critical: highest severity active alert (if any)
    """
    # Validate service name if provided
    service_filter = ""
    if service_name:
        service_filter = validate_service_name(service_name)

    # Filter alerts
    filtered = list(MOCK_ALERTS)
    if service_filter:
        filtered = [a for a in filtered if a["service_name"] == service_filter]

    # Separate by status
    active_alerts = [dict(a) for a in filtered if a.get("status") == "open"]
    resolved_alerts = [dict(a) for a in filtered if a.get("status") == "resolved"]

    # Count by severity
    alerts_by_severity: dict[str, int] = {}
    for a in filtered:
        sev = a.get("severity", "unknown")
        alerts_by_severity[sev] = alerts_by_severity.get(sev, 0) + 1

    # Count by service
    alerts_by_service: dict[str, int] = {}
    for a in filtered:
        svc = a.get("service_name", "unknown")
        alerts_by_service[svc] = alerts_by_service.get(svc, 0) + 1

    # Count by status
    alerts_by_status: dict[str, int] = {
        "open": len(active_alerts),
        "resolved": len(resolved_alerts),
    }

    # Find most critical active alert
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    most_critical = None
    if active_alerts:
        most_critical = dict(max(
            active_alerts,
            key=lambda a: severity_rank.get(a.get("severity", ""), 0),
        ))

    return {
        "total_count": len(filtered),
        "active_count": len(active_alerts),
        "resolved_count": len(resolved_alerts),
        "alerts_by_severity": alerts_by_severity,
        "alerts_by_service": alerts_by_service,
        "alerts_by_status": alerts_by_status,
        "active_alerts": active_alerts,
        "resolved_alerts": resolved_alerts,
        "most_critical": most_critical,
    }


# ── Standalone Entry Point (optional — for running individually) ──
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8010, path="/mcp")