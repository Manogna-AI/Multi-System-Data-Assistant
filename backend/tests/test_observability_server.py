"""
Tests for the 🔵 Observability MCP Server tool functions.

These tests call the FastMCP tool functions DIRECTLY as Python functions.
This is valid for unit testing the tool logic (validation, filtering, limits).
The MCP protocol transport layer (Streamable HTTP) is tested separately
via integration tests.

Properties tested: Read-Only · Time Validated · Size Limited
"""

import pytest

from app.utils.errors import DomainValidationError
from mcp_servers.observability_server import get_alerts, get_logs, get_metrics


# ── get_logs Tests ────────────────────────────────────────────────────────

def test_get_logs_valid_request():
    """Valid request returns logs for the specified service and time range."""
    logs = get_logs("payment-service", "2026-06-03T00:00:00Z", "2026-06-03T23:59:59Z")
    assert logs
    assert all(log["service_name"] == "payment-service" for log in logs)


def test_get_logs_rejects_invalid_service():
    """Non-allowlisted service name is rejected."""
    with pytest.raises(DomainValidationError):
        get_logs("unknown-service", "2026-06-03T00:00:00Z", "2026-06-03T23:59:59Z")


def test_get_logs_rejects_large_window():
    """Time window exceeding max_time_window_hours is rejected."""
    with pytest.raises(DomainValidationError):
        get_logs("payment-service", "2026-06-01T00:00:00Z", "2026-06-03T23:59:59Z")


def test_get_logs_rejects_invalid_time_format():
    """Invalid time format is rejected."""
    with pytest.raises(DomainValidationError):
        get_logs("payment-service", "2026/06/03", "2026/06/04")


def test_get_logs_rejects_end_before_start():
    """end_time before start_time is rejected."""
    with pytest.raises(DomainValidationError):
        get_logs("payment-service", "2026-06-03T23:59:59Z", "2026-06-03T00:00:00Z")


def test_get_logs_returns_empty_for_no_match():
    """Valid request with no matching logs returns empty list."""
    logs = get_logs("orders-service", "2026-06-01T00:00:00Z", "2026-06-01T23:59:59Z")
    assert logs == []


# ── get_metrics Tests ─────────────────────────────────────────────────────

def test_get_metrics_valid_request():
    """Valid request returns metric data with expected fields."""
    metric = get_metrics("payment-service", "error_rate", "24h")
    assert metric["value"] == 4.8
    assert metric["unit"] == "percent"
    assert metric["baseline"] == 0.7


def test_get_metrics_returns_null_for_unknown_metric():
    """Unknown metric name returns dict with None values."""
    metric = get_metrics("payment-service", "unknown_metric", "24h")
    assert metric["value"] is None
    assert metric["unit"] is None


def test_get_metrics_rejects_invalid_window():
    """Invalid window value is rejected."""
    with pytest.raises(DomainValidationError):
        get_metrics("payment-service", "error_rate", "48h")


# ── get_alerts Tests ──────────────────────────────────────────────────────

def test_get_alerts_valid_request():
    """Valid request returns alerts with expected fields."""
    alerts = get_alerts("payment-service")
    assert alerts
    assert alerts[0]["severity"] == "critical"
    assert alerts[0]["status"] == "open"


def test_get_alerts_rejects_invalid_service():
    """Non-allowlisted service is rejected."""
    with pytest.raises(DomainValidationError):
        get_alerts("bad-service")


def test_get_alerts_returns_empty_for_clean_service():
    """Service with no alerts returns empty list."""
    alerts = get_alerts("orders-service")
    assert alerts == []