import pytest
from app.utils.errors import DomainValidationError
from mcp_servers.observability_server import get_alerts, get_logs, get_metrics


def test_get_logs_valid_request():
    logs = get_logs("payment-service", "2026-06-03T00:00:00Z", "2026-06-03T23:59:59Z")
    assert logs
    assert all(log["service_name"] == "payment-service" for log in logs)


def test_get_logs_rejects_invalid_service():
    with pytest.raises(DomainValidationError):
        get_logs("unknown", "2026-06-03T00:00:00Z", "2026-06-03T23:59:59Z")


def test_get_logs_rejects_large_window():
    with pytest.raises(DomainValidationError):
        get_logs("payment-service", "2026-06-01T00:00:00Z", "2026-06-03T23:59:59Z")


def test_get_metrics_and_alerts_valid():
    metric = get_metrics("payment-service", "error_rate", "24h")
    alerts = get_alerts("payment-service")
    assert metric["value"] == 4.8
    assert alerts[0]["severity"] == "critical"
