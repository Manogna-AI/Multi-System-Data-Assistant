"""
🔴 Action MCP Server (Controlled) — FastMCP with Streamable HTTP Transport.

Exposes safe system action tools via MCP protocol:
  - restart_service(service_name, confirm) → dict
  - create_ticket(title, description, priority, confirm) → dict
  - scale_service(service_name, replicas, confirm) → dict

Properties: Confirmation · Allowlist · Logged
CRITICAL: All actions require explicit confirm=True flag.

Architecture Mapping:
  MCP TOOLS LAYER → 🔴 Action Server
  Mounted into gateway.py for unified access.

References:
  - FastMCP Composition: https://fastmcp.wiki/en/servers/composition
  - FastMCP: https://gofastmcp.com
"""

from fastmcp import FastMCP

from app.data.action_log_store import record_action
from app.utils.validators import (
    require_confirmation,
    validate_priority,
    validate_replicas,
    validate_service_name,
)


def create_mcp_server():
    if FastMCP is None:
        raise RuntimeError("FastMCP not installed")
    return FastMCP("action-server")

# ── FastMCP Server Instance (mounted by gateway.py) ──────────────
mcp = create_mcp_server()


def _reject(action_type: str, parameters: dict, reason: str) -> dict:
    """Log and return a rejection response for failed validation."""
    return record_action(
        action_type=action_type,
        parameters=parameters,
        status="rejected",
        reason=reason,
    )


@mcp.tool()
def restart_service(service_name: str, confirm: bool) -> dict:
    """Restart a microservice. Requires confirm=True and service must be in allowlist.

    Args:
        service_name: Target service (must be in allowlist).
        confirm: Must be True to execute. False = rejection.

    Returns:
        Dict with action_id, status (accepted/rejected), and reason.
    """
    params = {"service_name": service_name, "confirm": confirm}
    try:
        require_confirmation(confirm)
        service = validate_service_name(service_name)
    except ValueError as exc:
        return _reject("restart_service", params, str(exc))
    return record_action(
        action_type="restart_service",
        parameters={"service_name": service},
        status="accepted",
        reason=f"Restart scheduled safely for {service}.",
    )


@mcp.tool()
def create_ticket(
    title: str, description: str, priority: str, confirm: bool
) -> dict:
    """Create an incident/investigation ticket. Requires confirmation.

    Args:
        title: Ticket title (required).
        description: Ticket description (required).
        priority: Ticket priority (low, medium, high, critical).
        confirm: Must be True to execute.

    Returns:
        Dict with action_id, status (accepted/rejected), and reason.
    """
    params = {
        "title": title,
        "description": description,
        "priority": priority,
        "confirm": confirm,
    }
    try:
        require_confirmation(confirm)
        prio = validate_priority(priority)
    except ValueError as exc:
        return _reject("create_ticket", params, str(exc))
    return record_action(
        action_type="create_ticket",
        parameters={"title": title, "description": description, "priority": prio},
        status="accepted",
        reason=f"Ticket '{title}' created with priority {prio}.",
    )


@mcp.tool()
def scale_service(service_name: str, replicas: int, confirm: bool) -> dict:
    """Scale a service to N replicas. Requires confirmation and allowlist check.

    Args:
        service_name: Target service (must be in allowlist).
        replicas: Target replica count (1-5).
        confirm: Must be True to execute.

    Returns:
        Dict with action_id, status (accepted/rejected), and reason.
    """
    params = {
        "service_name": service_name,
        "replicas": replicas,
        "confirm": confirm,
    }
    try:
        require_confirmation(confirm)
        service = validate_service_name(service_name)
        rep = validate_replicas(replicas)
    except ValueError as exc:
        return _reject("scale_service", params, str(exc))
    return record_action(
        action_type="scale_service",
        parameters={"service_name": service, "replicas": rep},
        status="accepted",
        reason=f"Scaled {service} to {rep} replicas.",
    )


# ── Standalone Entry Point (optional — for running individually) ──
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8012, path="/mcp")