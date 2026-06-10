from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.adk_runner_service import QueryResult


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_query_result():
    return QueryResult(
        response="Analysis shows 3 declined transactions linked to payment-service errors.",
        session_id="test-session-456",
        agent_name="data_analyst_assistant",
        events_count=5,
        error=None,
    )


@patch("app.services.chat_service._get_adk_service")
def test_chat_api_returns_structured_response(mock_get_service, client, mock_query_result):
    mock_service = AsyncMock()
    mock_service.query.return_value = mock_query_result
    mock_get_service.return_value = mock_service

    response = client.post(
        "/chat/query",
        json={"query": "Compare system errors vs customer impact.", "user_id": "test_user"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "session_id" in body
    assert "agent_name" in body
    assert "events_count" in body
    assert body["session_id"] == "test-session-456"
    assert body["agent_name"] == "data_analyst_assistant"
    assert body["events_count"] == 5
    assert body["error"] is None


@patch("app.services.chat_service._get_adk_service")
def test_chat_api_passes_query_to_adk_service(mock_get_service, client):
    mock_service = AsyncMock()
    mock_service.query.return_value = QueryResult(
        response="Test response",
        session_id="sess-789",
        agent_name="observability_agent",
        events_count=2,
    )
    mock_get_service.return_value = mock_service

    response = client.post(
        "/chat/query",
        json={
            "query": "Show me error logs for payment-service",
            "user_id": "user_42",
            "session_id": "existing-session-001",
        },
    )

    assert response.status_code == 200
    mock_service.query.assert_called_once_with(
        user_id="user_42",
        message="Show me error logs for payment-service",
        session_id="existing-session-001",
    )


@patch("app.services.chat_service._get_adk_service")
def test_chat_api_creates_new_session_when_none_provided(mock_get_service, client):
    mock_service = AsyncMock()
    mock_service.query.return_value = QueryResult(
        response="New session response",
        session_id="new-auto-session",
        agent_name="business_data_agent",
        events_count=4,
    )
    mock_get_service.return_value = mock_service

    response = client.post(
        "/chat/query",
        json={"query": "Show me orders for CUST-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "new-auto-session"


@patch("app.services.chat_service._get_adk_service")
def test_chat_api_returns_error_on_failure(mock_get_service, client):
    mock_service = AsyncMock()
    mock_service.query.return_value = QueryResult(
        response="An error occurred while processing your request: Ollama not reachable",
        session_id="err-session",
        agent_name=None,
        events_count=0,
        error="Ollama not reachable",
    )
    mock_get_service.return_value = mock_service

    response = client.post(
        "/chat/query",
        json={"query": "Show me metrics", "user_id": "test_user"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] == "Ollama not reachable"
    assert body["events_count"] == 0


@patch("app.services.chat_service._get_adk_service")
def test_chat_api_rejects_empty_query(mock_get_service, client):
    mock_service = AsyncMock()
    mock_get_service.return_value = mock_service

    response = client.post(
        "/chat/query",
        json={"query": "", "user_id": "test_user"},
    )
    assert response.status_code == 422


@patch("app.services.chat_service._get_adk_service")
def test_chat_api_rejects_too_long_query(mock_get_service, client):
    mock_service = AsyncMock()
    mock_get_service.return_value = mock_service

    response = client.post(
        "/chat/query",
        json={"query": "x" * 2001, "user_id": "test_user"},
    )
    assert response.status_code == 422


@patch("app.services.chat_service._get_adk_service")
def test_chat_api_uses_default_user_id(mock_get_service, client):
    mock_service = AsyncMock()
    mock_service.query.return_value = QueryResult(
        response="Default user response",
        session_id="default-sess",
    )
    mock_get_service.return_value = mock_service

    response = client.post(
        "/chat/query",
        json={"query": "Hello"},
    )

    assert response.status_code == 200
    mock_service.query.assert_called_once()
    call_args = mock_service.query.call_args
    assert call_args.kwargs["user_id"] == "default_user"