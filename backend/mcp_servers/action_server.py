"""
🔴 Action MCP Server (Controlled) — FastMCP with Streamable HTTP Transport.

Exposes safe system action tools via MCP protocol:

  Existing Tools:
  - restart_service(service_name, confirm) → dict
  - create_ticket(title, description, priority, confirm) → dict (enhanced)
  - scale_service(service_name, replicas, confirm) → dict

  New Tools:
  - list_tickets(status, priority, service_name) → dict
  - get_ticket(ticket_id) → dict
  - update_ticket(ticket_id, priority, status, assigned_to, confirm) → dict
  - get_audit_log(action_type, service_name) → dict

Properties: Confirmation · Allowlist · Logged · Ticket Management
CRITICAL: All state-changing actions require explicit confirm=True flag.

Architecture Mapping:
  MCP TOOLS LAYER → 🔴 Action Server
  Mounted into gateway.py for unified access.

References:
  - FastMCP Composition: https://fastmcp.wiki/en/servers/composition
  - FastMCP: https://gofastmcp.com
"""

from fastmcp import FastMCP

from app.data.action_log_store import (
    record_action,
    list_actions,
    create_ticket as store_ticket,
    list_tickets as fetch_tickets,
    get_ticket as fetch_ticket,
    update_ticket as modify_ticket,
)
from app.utils.validators import (
    require_confirmation,
    validate_priority,
    validate_replicas,
    validate_service_name,
)


# ── FastMCP Server Instance (mounted by gateway.py) ──────────────

def create_mcp_server():
    """
    Create and return the FastMCP server instance for the Action MCP server.

    This factory function encapsulates MCP server creation so that server
    initialization is defined in one place and can be extended later if
    additional startup configuration is needed.

    Returns:
        FastMCP: The initialized MCP server instance for action tools.

    Raises:
        RuntimeError: If the FastMCP library is unavailable in the current
            environment.
    """
    if FastMCP is None:
        raise RuntimeError("FastMCP not installed")
    return FastMCP("action-server")


mcp = create_mcp_server()


def _reject(action_type: str, parameters: dict, reason: str) -> dict:
    """Log and return a rejection response for failed validation."""
    return record_action(
        action_type=action_type,
        parameters=parameters,
        status="rejected",
        reason=reason,
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXISTING TOOLS (restart_service and scale_service unchanged,
#                 create_ticket enhanced to also store in ticket store)
# ═══════════════════════════════════════════════════════════════════════════


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
    title: str,
    description: str,
    priority: str,
    confirm: bool,
    service_name: str = "",
) -> dict:
    """Create an incident/investigation ticket. Requires confirmation.

    Creates the ticket in the ticket store AND records the action
    in the audit log.

    Args:
        title: Ticket title (required).
        description: Ticket description (required).
        priority: Ticket priority (low, medium, high, critical).
        confirm: Must be True to execute.
        service_name: Optional related service name.

    Returns:
        Dict with action_id, ticket_id, status (accepted/rejected), and reason.
    """
    params = {
        "title": title,
        "description": description,
        "priority": priority,
        "confirm": confirm,
        "service_name": service_name,
    }
    try:
        require_confirmation(confirm)
        prio = validate_priority(priority)
    except ValueError as exc:
        return _reject("create_ticket", params, str(exc))

    # Validate service name if provided (optional field)
    validated_service = ""
    if service_name:
        try:
            validated_service = validate_service_name(service_name)
        except ValueError:
            # Service name is optional for tickets — allow non-allowlisted values
            validated_service = service_name.strip().lower()

    # Store ticket in the ticket store
    ticket = store_ticket(
        title=title,
        description=description,
        priority=prio,
        service_name=validated_service,
    )

    # Record action in audit log
    action = record_action(
        action_type="create_ticket",
        parameters={
            "title": title,
            "description": description,
            "priority": prio,
            "service_name": validated_service,
            "ticket_id": ticket["ticket_id"],
        },
        status="accepted",
        reason=f"Ticket '{title}' created as {ticket['ticket_id']} with priority {prio}.",
    )

    # Combine action and ticket info
    action["ticket_id"] = ticket["ticket_id"]
    return action


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


# ═══════════════════════════════════════════════════════════════════════════
# NEW TOOLS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_tickets(
    status: str = "",
    priority: str = "",
    service_name: str = "",
) -> dict:
    """List tickets with optional status, priority, and service filters.

    Supports queries like:
      - "Show all open tickets"
      - "Show critical tickets"
      - "How many tickets are open?"
      - "Show tickets for payment-service"
      - "Show resolved high priority tickets"
      - "List all tickets"

    Args:
        status: Optional status filter (open, in_progress, resolved, closed).
                Case-insensitive. Empty string = all statuses.
        priority: Optional priority filter (low, medium, high, critical).
                  Case-insensitive. Empty string = all priorities.
        service_name: Optional service name filter.
                      Empty string = all services.

    Returns:
        Dict with:
          - total_count: number of matching tickets
          - tickets: list of matching ticket dicts
          - count_by_status: breakdown by status
          - count_by_priority: breakdown by priority
          - message: helper message
    """
    # Validate status if provided
    allowed_statuses = {"open", "in_progress", "resolved", "closed"}
    normalized_status = ""
    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in allowed_statuses:
            return {
                "total_count": 0,
                "tickets": [],
                "count_by_status": {},
                "count_by_priority": {},
                "message": f"Invalid status '{status}'. Must be one of: {sorted(allowed_statuses)}",
            }

    # Validate priority if provided
    normalized_priority = ""
    if priority:
        normalized_priority = priority.strip().lower()
        allowed_priorities = {"low", "medium", "high", "critical"}
        if normalized_priority not in allowed_priorities:
            return {
                "total_count": 0,
                "tickets": [],
                "count_by_status": {},
                "count_by_priority": {},
                "message": f"Invalid priority '{priority}'. Must be one of: {sorted(allowed_priorities)}",
            }

    # Fetch tickets with filters
    tickets = fetch_tickets(
        status=normalized_status,
        priority=normalized_priority,
        service_name=service_name.strip().lower() if service_name else "",
    )

    # Count by status
    count_by_status: dict[str, int] = {}
    for t in tickets:
        st = t.get("status", "unknown")
        count_by_status[st] = count_by_status.get(st, 0) + 1

    # Count by priority
    count_by_priority: dict[str, int] = {}
    for t in tickets:
        p = t.get("priority", "unknown")
        count_by_priority[p] = count_by_priority.get(p, 0) + 1

    # Build message
    filters_desc = []
    if normalized_status:
        filters_desc.append(f"status={normalized_status}")
    if normalized_priority:
        filters_desc.append(f"priority={normalized_priority}")
    if service_name:
        filters_desc.append(f"service={service_name}")

    if tickets:
        filter_text = f" matching filters: {', '.join(filters_desc)}" if filters_desc else ""
        message = f"Found {len(tickets)} ticket(s){filter_text}."
    else:
        filter_text = f" matching filters: {', '.join(filters_desc)}" if filters_desc else ""
        message = f"No tickets found{filter_text}."

    return {
        "total_count": len(tickets),
        "tickets": tickets,
        "count_by_status": count_by_status,
        "count_by_priority": count_by_priority,
        "message": message,
    }


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Get a single ticket by ticket ID.

    Supports queries like:
      - "Show ticket TKT-001"
      - "Get details for ticket TKT-003"
      - "What is the status of TKT-002?"

    Args:
        ticket_id: Ticket identifier (TKT-### format).

    Returns:
        Dict with full ticket details.
        Returns {found: False} if ticket not found.
    """
    if not ticket_id or not ticket_id.strip():
        return {
            "found": False,
            "message": "Please provide a ticket ID (e.g., TKT-001).",
        }

    ticket = fetch_ticket(ticket_id.strip())

    if ticket is None:
        return {
            "found": False,
            "ticket_id": ticket_id.strip().upper(),
            "message": f"Ticket '{ticket_id.strip().upper()}' not found.",
        }

    return {
        "found": True,
        **ticket,
    }


@mcp.tool()
def update_ticket(
    ticket_id: str,
    confirm: bool,
    priority: str = "",
    status: str = "",
    assigned_to: str = "",
) -> dict:
    """Update an existing ticket. Requires confirmation.

    Supports queries like:
      - "Update ticket TKT-001 priority to critical"
      - "Close ticket TKT-003"
      - "Mark TKT-002 as resolved"
      - "Assign TKT-001 to ops_team"

    Args:
        ticket_id: Ticket identifier (TKT-### format).
        confirm: Must be True to execute.
        priority: New priority (low, medium, high, critical). Optional.
        status: New status (open, in_progress, resolved, closed). Optional.
        assigned_to: New assignee. Optional.

    Returns:
        Dict with updated ticket details and action audit record.
    """
    params = {
        "ticket_id": ticket_id,
        "priority": priority,
        "status": status,
        "assigned_to": assigned_to,
        "confirm": confirm,
    }

    try:
        require_confirmation(confirm)
    except ValueError as exc:
        return _reject("update_ticket", params, str(exc))

    # Validate priority if provided
    validated_priority = ""
    if priority:
        try:
            validated_priority = validate_priority(priority)
        except ValueError as exc:
            return _reject("update_ticket", params, str(exc))

    # Validate status if provided
    allowed_statuses = {"open", "in_progress", "resolved", "closed"}
    validated_status = ""
    if status:
        validated_status = status.strip().lower()
        if validated_status not in allowed_statuses:
            return _reject(
                "update_ticket",
                params,
                f"status must be one of {sorted(allowed_statuses)}",
            )

    # Check at least one update field is provided
    if not priority and not status and not assigned_to:
        return _reject(
            "update_ticket",
            params,
            "At least one of priority, status, or assigned_to must be provided.",
        )

    # Perform update
    updated = modify_ticket(
        ticket_id=ticket_id.strip(),
        priority=validated_priority,
        status=validated_status,
        assigned_to=assigned_to.strip() if assigned_to else "",
    )

    if updated is None:
        return _reject(
            "update_ticket",
            params,
            f"Ticket '{ticket_id.strip().upper()}' not found.",
        )

    # Record action in audit log
    changes = []
    if validated_priority:
        changes.append(f"priority={validated_priority}")
    if validated_status:
        changes.append(f"status={validated_status}")
    if assigned_to:
        changes.append(f"assigned_to={assigned_to.strip()}")

    action = record_action(
        action_type="update_ticket",
        parameters={
            "ticket_id": updated["ticket_id"],
            "changes": ", ".join(changes),
        },
        status="accepted",
        reason=f"Ticket {updated['ticket_id']} updated: {', '.join(changes)}.",
    )

    action["updated_ticket"] = updated
    return action


@mcp.tool()
def get_audit_log(
    action_type: str = "",
    service_name: str = "",
) -> dict:
    """Retrieve action history / audit trail with optional filters.

    Supports queries like:
      - "Show action history"
      - "Show all restarts"
      - "When was payment-service last restarted?"
      - "Show all ticket creation actions"
      - "Show rejected actions"
      - "Show scaling history for payment-service"

    Args:
        action_type: Optional filter (restart_service, scale_service,
                     create_ticket, update_ticket).
                     Empty string = all action types.
        service_name: Optional service name filter.
                      Empty string = all services.

    Returns:
        Dict with:
          - total_count: number of matching audit entries
          - actions: list of audit log entries (most recent first)
          - count_by_type: breakdown by action type
          - count_by_status: breakdown by status (accepted/rejected)
          - message: helper message
    """
    # Normalize filters
    normalized_type = action_type.strip().lower() if action_type else ""
    normalized_service = service_name.strip().lower() if service_name else ""

    # Validate action type if provided
    allowed_types = {
        "restart_service", "scale_service",
        "create_ticket", "update_ticket",
    }
    if normalized_type and normalized_type not in allowed_types:
        return {
            "total_count": 0,
            "actions": [],
            "count_by_type": {},
            "count_by_status": {},
            "message": f"Invalid action_type '{action_type}'. Must be one of: {sorted(allowed_types)}",
        }

    # Fetch actions with filters
    actions = list_actions(
        action_type=normalized_type,
        service_name=normalized_service,
    )

    # Count by type
    count_by_type: dict[str, int] = {}
    for a in actions:
        at = a.get("action_type", "unknown")
        count_by_type[at] = count_by_type.get(at, 0) + 1

    # Count by status
    count_by_status: dict[str, int] = {}
    for a in actions:
        st = a.get("status", "unknown")
        count_by_status[st] = count_by_status.get(st, 0) + 1

    # Build message
    filters_desc = []
    if normalized_type:
        filters_desc.append(f"type={normalized_type}")
    if normalized_service:
        filters_desc.append(f"service={normalized_service}")

    if actions:
        filter_text = f" matching filters: {', '.join(filters_desc)}" if filters_desc else ""
        message = f"Found {len(actions)} action(s){filter_text}."
    else:
        filter_text = f" matching filters: {', '.join(filters_desc)}" if filters_desc else ""
        message = f"No actions found{filter_text}."

    return {
        "total_count": len(actions),
        "actions": actions,
        "count_by_type": count_by_type,
        "count_by_status": count_by_status,
        "message": message,
    }


# ── Standalone Entry Point (optional — for running individually) ──
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8012, path="/mcp")