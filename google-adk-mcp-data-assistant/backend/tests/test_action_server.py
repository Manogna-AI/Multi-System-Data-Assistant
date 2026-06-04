from app.data.action_log_store import clear_actions, list_actions
from mcp_servers.action_server import restart_service, scale_service


def test_action_rejected_without_confirmation():
    clear_actions()
    result = restart_service("payment-service", False)
    assert result["status"] == "rejected"
    assert "confirm=True" in result["reason"]
    assert list_actions()[0]["status"] == "rejected"


def test_action_rejected_for_non_allowlisted_service():
    clear_actions()
    result = restart_service("bad-service", True)
    assert result["status"] == "rejected"
    assert list_actions()[0]["status"] == "rejected"


def test_action_logged_when_accepted():
    clear_actions()
    result = restart_service("payment-service", True)
    assert result["status"] == "accepted"
    logs = list_actions()
    assert logs and logs[0]["action_type"] == "restart_service"


def test_scale_rejects_unsafe_replicas():
    clear_actions()
    result = scale_service("payment-service", 9, True)
    assert result["status"] == "rejected"
