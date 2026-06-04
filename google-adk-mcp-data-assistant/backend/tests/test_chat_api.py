from fastapi.testclient import TestClient
from app.main import app


def test_chat_api_returns_structured_response():
    client = TestClient(app)
    response = client.post("/chat/query", json={"query": "Compare system errors vs customer impact."})
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "CROSS_QUERY"
    assert isinstance(body["tool_trace"], list)
    assert "action_confirmation" in body


def test_action_query_requires_confirmation_and_rejects_without_confirm():
    client = TestClient(app)
    response = client.post("/chat/query", json={"query": "Restart payment service", "confirm_action": False})
    assert response.status_code == 200
    body = response.json()
    assert body["action_confirmation"]["required"] is True
    assert body["data"]["action"]["action_result"]["status"] == "rejected"
