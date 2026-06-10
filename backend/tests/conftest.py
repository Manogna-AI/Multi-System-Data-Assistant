"""
Shared pytest configuration and fixtures for the test suite.

Adds the backend root to sys.path so both `app.*` and `mcp_servers.*`
imports work correctly in all test files.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── Path Setup ────────────────────────────────────────────────────────────
# tests/ is inside backend/, so parents[1] = backend/
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# ── Shared Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def settings():
    """Provides a test Settings instance with safe defaults."""
    from app.config import Settings

    return Settings(
        llm_model="ollama_chat/qwen3:1.7b",
        ollama_base_url="http://localhost:11434",
        observability_mcp_url="http://localhost:8010/mcp",
        business_mcp_url="http://localhost:8011/mcp",
        action_mcp_url="http://localhost:8012/mcp",
        allowed_services=[
            "payment-service",
            "checkout-service",
            "orders-service",
            "inventory-service",
        ],
        max_time_window_hours=24,
        max_log_results=50,
    )


@pytest.fixture
def mock_adk_runner_service():
    """Provides a mocked AdkRunnerService for chat API tests.

    This avoids needing running Ollama + MCP servers during unit tests.
    The mock returns a realistic QueryResult without invoking ADK.
    """
    from app.services.adk_runner_service import QueryResult

    mock_service = AsyncMock()
    mock_service.query.return_value = QueryResult(
        response="This is a test response from the mocked ADK agent.",
        session_id="test-session-123",
        agent_name="data_analyst_assistant",
        events_count=3,
        error=None,
    )
    mock_service.health_check.return_value = {
        "status": "healthy",
        "root_agent": "data_analyst_assistant",
    }
    return mock_service