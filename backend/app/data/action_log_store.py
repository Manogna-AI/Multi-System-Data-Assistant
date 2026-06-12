"""
Action Mock Data — Audit Logs and Ticket Store.

Designed to support a wide range of user queries:
  - Action execution: restart, scale, create ticket
  - Ticket management: list, filter by status/priority
  - Audit trail: action history, filtered by type/service
  - Service configuration: replica counts, maintenance mode

Data relationships:
  - Pre-populated audit log with 5 historical entries
  - Pre-populated ticket store with 6 tickets across 4 statuses
  - Thread-safe access via Lock
"""

from datetime import datetime, timezone, timedelta
from threading import Lock
from uuid import uuid4

_now = datetime.now(timezone.utc)
_1h_ago = (_now - timedelta(hours=1)).isoformat()
_3h_ago = (_now - timedelta(hours=3)).isoformat()
_yesterday = (_now - timedelta(days=1)).isoformat()
_2_days_ago = (_now - timedelta(days=2)).isoformat()
_3_days_ago = (_now - timedelta(days=3)).isoformat()


# ── Audit Log ─────────────────────────────────────────────────────────────
# Pre-populated with 5 historical action entries
_ACTION_LOGS: list[dict] = [
    {
        "action_id": "ACT-001",
        "action_type": "restart",
        "parameters": {"service_name": "payment-service"},
        "status": "accepted",
        "reason": None,
        "performed_by": "default_user",
        "created_at": _2_days_ago,
    },
    {
        "action_id": "ACT-002",
        "action_type": "scale",
        "parameters": {"service_name": "payment-service", "replicas": 3},
        "status": "accepted",
        "reason": None,
        "performed_by": "default_user",
        "created_at": _2_days_ago,
    },
    {
        "action_id": "ACT-003",
        "action_type": "restart",
        "parameters": {"service_name": "database-master"},
        "status": "rejected",
        "reason": "service_name must be one of [payment-service, checkout-service, orders-service, inventory-service]",
        "performed_by": "default_user",
        "created_at": _yesterday,
    },
    {
        "action_id": "ACT-004",
        "action_type": "ticket",
        "parameters": {"title": "Payment gateway timeout", "priority": "high"},
        "status": "accepted",
        "reason": None,
        "performed_by": "default_user",
        "created_at": _yesterday,
    },
    {
        "action_id": "ACT-005",
        "action_type": "restart",
        "parameters": {"service_name": "inventory-service"},
        "status": "accepted",
        "reason": None,
        "performed_by": "default_user",
        "created_at": _3h_ago,
    },
]

_ACTION_LOCK = Lock()


def record_action(
    action_type: str,
    parameters: dict,
    status: str,
    reason: str | None = None,
    performed_by: str = "default_user",
) -> dict:
    """Record a new action in the audit log.

    Args:
        action_type: Type of action (restart, scale, ticket).
        parameters: Action parameters dict.
        status: Result status (accepted, rejected).
        reason: Rejection reason (if applicable).
        performed_by: User who performed the action.

    Returns:
        The created audit log entry dict.
    """
    entry = {
        "action_id": f"ACT-{str(uuid4())[:8].upper()}",
        "action_type": action_type,
        "parameters": parameters,
        "status": status,
        "reason": reason,
        "performed_by": performed_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _ACTION_LOCK:
        _ACTION_LOGS.append(entry)
    return entry


def list_actions(
    action_type: str = "",
    service_name: str = "",
    limit: int = 100,
) -> list[dict]:
    """Retrieve action history with optional filters.

    Args:
        action_type: Optional filter (restart, scale, ticket).
        service_name: Optional service name filter.
        limit: Maximum number of entries to return.

    Returns:
        List of audit log entries, most recent first.
    """
    with _ACTION_LOCK:
        results = list(reversed(_ACTION_LOGS))

    if action_type:
        results = [r for r in results if r["action_type"] == action_type]

    if service_name:
        results = [
            r for r in results
            if r.get("parameters", {}).get("service_name", "") == service_name
        ]

    return results[:limit]


def clear_actions() -> None:
    """Clear all audit log entries."""
    with _ACTION_LOCK:
        _ACTION_LOGS.clear()


# ── Ticket Store ──────────────────────────────────────────────────────────
# Pre-populated with 6 tickets across 4 statuses and 4 priorities
# Statuses: open, in_progress, resolved, closed
# Priorities: low, medium, high, critical
_TICKETS: list[dict] = [
    {
        "ticket_id": "TKT-001",
        "title": "Payment gateway authorization timeouts",
        "description": "Card authorization failing with 504 timeout from gateway",
        "priority": "critical",
        "status": "open",
        "service_name": "payment-service",
        "created_by": "default_user",
        "assigned_to": None,
        "created_at": _3h_ago,
        "updated_at": _3h_ago,
    },
    {
        "ticket_id": "TKT-002",
        "title": "Checkout callback 503 errors",
        "description": "Checkout service receiving 503 from payment callbacks",
        "priority": "high",
        "status": "open",
        "service_name": "checkout-service",
        "created_by": "default_user",
        "assigned_to": None,
        "created_at": _yesterday,
        "updated_at": _yesterday,
    },
    {
        "ticket_id": "TKT-003",
        "title": "Inventory sync delay with warehouse API",
        "description": "Stock synchronization delayed beyond 30 minute threshold",
        "priority": "medium",
        "status": "in_progress",
        "service_name": "inventory-service",
        "created_by": "default_user",
        "assigned_to": "ops_team",
        "created_at": _yesterday,
        "updated_at": _1h_ago,
    },
    {
        "ticket_id": "TKT-004",
        "title": "Payment database connection pool tuning",
        "description": "Connection pool exhaustion observed — need to increase max connections",
        "priority": "high",
        "status": "resolved",
        "service_name": "payment-service",
        "created_by": "default_user",
        "assigned_to": "dba_team",
        "created_at": _2_days_ago,
        "updated_at": _yesterday,
    },
    {
        "ticket_id": "TKT-005",
        "title": "Order queue monitoring dashboard",
        "description": "Create monitoring dashboard for order queue depth and processing rate",
        "priority": "low",
        "status": "open",
        "service_name": "orders-service",
        "created_by": "default_user",
        "assigned_to": None,
        "created_at": _3_days_ago,
        "updated_at": _3_days_ago,
    },
    {
        "ticket_id": "TKT-006",
        "title": "Checkout latency optimization",
        "description": "P95 latency at 1800ms — investigate and optimize checkout flow",
        "priority": "medium",
        "status": "closed",
        "service_name": "checkout-service",
        "created_by": "default_user",
        "assigned_to": "perf_team",
        "created_at": _3_days_ago,
        "updated_at": _2_days_ago,
    },
]

_TICKET_LOCK = Lock()
_TICKET_COUNTER = 6  # Next ticket number


def create_ticket(
    title: str,
    description: str,
    priority: str,
    service_name: str = "",
    created_by: str = "default_user",
) -> dict:
    """Create a new ticket in the ticket store.

    Args:
        title: Ticket title.
        description: Ticket description.
        priority: Priority level (low, medium, high, critical).
        service_name: Optional related service name.
        created_by: User who created the ticket.

    Returns:
        The created ticket dict.
    """
    global _TICKET_COUNTER
    with _TICKET_LOCK:
        _TICKET_COUNTER += 1
        ticket = {
            "ticket_id": f"TKT-{_TICKET_COUNTER:03d}",
            "title": title,
            "description": description,
            "priority": priority,
            "status": "open",
            "service_name": service_name,
            "created_by": created_by,
            "assigned_to": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _TICKETS.append(ticket)
    return ticket


def list_tickets(
    status: str = "",
    priority: str = "",
    service_name: str = "",
    limit: int = 50,
) -> list[dict]:
    """List tickets with optional filters.

    Args:
        status: Optional filter (open, in_progress, resolved, closed).
        priority: Optional filter (low, medium, high, critical).
        service_name: Optional service name filter.
        limit: Maximum number of tickets to return.

    Returns:
        List of ticket dicts, most recent first.
    """
    with _TICKET_LOCK:
        results = list(reversed(_TICKETS))

    if status:
        results = [t for t in results if t["status"] == status.lower()]

    if priority:
        results = [t for t in results if t["priority"] == priority.lower()]

    if service_name:
        results = [t for t in results if t["service_name"] == service_name]

    return results[:limit]


def get_ticket(ticket_id: str) -> dict | None:
    """Get a single ticket by ID.

    Args:
        ticket_id: Ticket identifier (TKT-###).

    Returns:
        Ticket dict or None if not found.
    """
    with _TICKET_LOCK:
        for ticket in _TICKETS:
            if ticket["ticket_id"] == ticket_id.upper():
                return dict(ticket)
    return None


def update_ticket(
    ticket_id: str,
    priority: str = "",
    status: str = "",
    assigned_to: str = "",
) -> dict | None:
    """Update an existing ticket.

    Args:
        ticket_id: Ticket identifier (TKT-###).
        priority: New priority (if provided).
        status: New status (if provided).
        assigned_to: New assignee (if provided).

    Returns:
        Updated ticket dict or None if not found.
    """
    with _TICKET_LOCK:
        for ticket in _TICKETS:
            if ticket["ticket_id"] == ticket_id.upper():
                if priority:
                    ticket["priority"] = priority.lower()
                if status:
                    ticket["status"] = status.lower()
                if assigned_to:
                    ticket["assigned_to"] = assigned_to
                ticket["updated_at"] = datetime.now(timezone.utc).isoformat()
                return dict(ticket)
    return None