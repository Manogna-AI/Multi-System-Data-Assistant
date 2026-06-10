"""
Tests for the 🔴 Action MCP Server tool functions.

Properties tested: Confirmation · Allowlist · Logged
CRITICAL: All actions require confirm=True and allowlisted service names.
"""

from app.data.action_log_store import clear_actions, list_actions
from mcp_servers.action_server import create_ticket, restart_service, scale_service


# ── Confirmation Guard Tests ──────────────────────────────────────────────

def test_action_rejected_without_confirmation():
    """Action is rejected when confirm=False — confirmation guard enforced."""
    clear_actions()
    result = restart_service("payment-service", False)
    assert result["status"] == "rejected"
    assert "confirm=True" in result["reason"]

    # Verify rejection is LOGGED in audit trail
    logs = list_actions()
    assert len(logs) == 1
    assert logs[0]["status"] == "rejected"
    assert logs[0]["action_type"] == "restart_service"


# ── Allowlist Tests ───────────────────────────────────────────────────────

def test_action_rejected_for_non_allowlisted_service():
    """Action is rejected for services not in the allowlist."""
    clear_actions()
    result = restart_service("bad-service", True)
    assert result["status"] == "rejected"

    # Verify rejection is LOGGED
    logs = list_actions()
    assert len(logs) == 1
    assert logs[0]["status"] == "rejected"


# ── Accepted Action Tests ─────────────────────────────────────────────────

def test_restart_accepted_and_logged():
    """Valid restart with confirmation is accepted and logged."""
    clear_actions()
    result = restart_service("payment-service", True)
    assert result["status"] == "accepted"
    assert "payment-service" in result["message"]

    # Verify action is LOGGED in audit trail
    logs = list_actions()
    assert len(logs) == 1
    assert logs[0]["action_type"] == "restart_service"
    assert logs[0]["status"] == "accepted"


# ── Scale Service Tests ───────────────────────────────────────────────────

def test_scale_rejects_unsafe_replicas():
    """Scale is rejected when replica count exceeds safe range (1-5)."""
    clear_actions()
    result = scale_service("payment-service", 9, True)
    assert result["status"] == "rejected"


def test_scale_accepted_within_safe_range():
    """Scale is accepted when replicas are within safe range."""
    clear_actions()
    result = scale_service("payment-service", 3, True)
    assert result["status"] == "accepted"
    assert "3 replicas" in result["message"]


def test_scale_rejected_without_confirmation():
    """Scale is rejected without confirm=True."""
    clear_actions()
    result = scale_service("payment-service", 2, False)
    assert result["status"] == "rejected"


# ── Create Ticket Tests ──────────────────────────────────────────────────

def test_create_ticket_accepted():
    """Valid ticket creation with confirmation is accepted."""
    clear_actions()
    result = create_ticket(
        title="Payment failures",
        description="Multiple payment authorization timeouts since 9 AM",
        priority="high",
        confirm=True,
    )
    assert result["status"] == "accepted"
    assert result["message"] == "Ticket created"

    # Verify logged
    logs = list_actions()
    assert len(logs) == 1
    assert logs[0]["action_type"] == "create_ticket"


def test_create_ticket_rejects_invalid_priority():
    """Ticket with invalid priority is rejected."""
    clear_actions()
    result = create_ticket(
        title="Test",
        description="Test description",
        priority="urgent",  # Not in: low, medium, high, critical
        confirm=True,
    )
    assert result["status"] == "rejected"


def test_create_ticket_rejects_empty_title():
    """Ticket with empty title is rejected."""
    clear_actions()
    result = create_ticket(
        title="",
        description="Some description",
        priority="low",
        confirm=True,
    )
    assert result["status"] == "rejected"


def test_create_ticket_rejected_without_confirmation():
    """Ticket creation without confirm=True is rejected."""
    clear_actions()
    result = create_ticket(
        title="Test",
        description="Test",
        priority="low",
        confirm=False,
    )
    assert result["status"] == "rejected"


# ── Audit Trail Completeness ─────────────────────────────────────────────

def test_all_actions_are_logged():
    """Verify that EVERY action (accepted or rejected) is logged."""
    clear_actions()

    restart_service("payment-service", False)   # rejected
    restart_service("bad-service", True)         # rejected
    restart_service("payment-service", True)     # accepted
    scale_service("payment-service", 3, True)    # accepted

    logs = list_actions()
    assert len(logs) == 4
    statuses = [log["status"] for log in logs]
    # Most recent first (list_actions returns reversed)
    assert statuses.count("accepted") == 2
    assert statuses.count("rejected") == 2