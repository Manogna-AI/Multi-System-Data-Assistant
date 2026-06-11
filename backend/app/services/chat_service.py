"""
Chat Service — FastAPI integration layer for the ADK-powered assistant.

This service bridges the FastAPI routes with the ADK Runner Service.
It handles:
  - Request validation and transformation
  - Session management (user_id, session_id)
  - Delegating to AdkRunnerService for agent execution
  - Mapping ADK ToolCall → ToolTraceItem for the frontend
  - Formatting ADK QueryResult → ChatQueryResponse for the frontend

Architecture Mapping:
  routes_chat.py → ChatService → AdkRunnerService → ADK Runner
    → Root Agent → Sub-agents → McpToolset → MCP Servers
"""

from __future__ import annotations

import logging
from typing import Optional
import re
from app.config import get_settings
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.schemas.common import ToolTraceItem
from app.services.adk_runner_service import AdkRunnerService

logger = logging.getLogger(__name__)

# ── Singleton ADK Runner Service ──────────────────────────────────────────
# Created once and reused across all requests.
# The Runner holds the root agent and session service.

_adk_service: Optional[AdkRunnerService] = None

def _finalize_answer(text: str) -> str:
    """Final UI-facing cleanup for agent responses."""
    if not text:
        return "No response from agent."

    unwanted_patterns = [
        r"(?im)^we can provide answer:.*$",
        r"(?im)^now format.*$",
        r"(?im)^analysis:.*$",
        r"(?im)^observation:.*$",
        r"(?im)^let me .*?$",
        r"(?im)^i will .*?$",
        r"(?im)^thus .*?$",
    ]

    for pattern in unwanted_patterns:
        text = re.sub(pattern, "", text).strip()

    return text.strip() or "No response from agent."


def _get_adk_service() -> AdkRunnerService:
    """Lazy singleton for AdkRunnerService."""
    global _adk_service
    if _adk_service is None:
        settings = get_settings()
        _adk_service = AdkRunnerService(settings)
    return _adk_service


class ChatService:
    """Orchestrates chat queries through the ADK agent pipeline.

    Responsibilities:
      1. Accept ChatQueryRequest from the route handler
      2. Delegate to AdkRunnerService for agent execution
      3. Map ADK ToolCall objects → ToolTraceItem Pydantic models
      4. Return ChatQueryResponse to the route handler

    This class does NOT contain any agent logic — that lives in
    adk_runner_service.py and the agent modules.
    """

    def __init__(self) -> None:
        self.adk_service = _get_adk_service()
        logger.info("ChatService initialized.")

    async def handle_query(self, request: ChatQueryRequest) -> ChatQueryResponse:
        """Process a chat query through the ADK agent pipeline.

        Args:
            request: Validated ChatQueryRequest with query, user_id, session_id.

        Returns:
            ChatQueryResponse with answer, tool_trace, session_id, agent_name.
        """
        logger.info("Processing chat query: '%s'", request.query[:80])

        try:
            # ── Execute via ADK Runner Service ────────────────
            result = await self.adk_service.query(
                user_id=request.user_id or "default_user",
                message=request.query,
                session_id=request.session_id,
            )

            # ── Map ToolCall → ToolTraceItem ──────────────────
            # adk_runner_service.ToolCall fields:
            #   .agent_name (str), .tool_name (str),
            #   .arguments (dict), .result (Any — usually dict)
            #
            # schemas/common.py ToolTraceItem fields:
            #   .agent (str), .tool (str),
            #   .arguments (dict), .result_summary (str)
            tool_trace = [
                ToolTraceItem(
                    agent=tc.agent_name,
                    tool=tc.tool_name,
                    arguments=tc.arguments,
                    result_summary=str(tc.result) if tc.result else "",
                )
                for tc in result.tool_calls
            ]

            # ── Build Response ────────────────────────────────
            answer = _finalize_answer(result.response)

            logger.info(
                "Chat response: agent=%s, tools=%d, answer_len=%d",
                result.agent_name,
                len(tool_trace),
                len(answer),
            )

            return ChatQueryResponse(
                answer=answer,
                session_id=result.session_id,
                agent_name=result.agent_name,
                tool_trace=tool_trace,
                events_count=result.events_count,
                error=None,
            )

        except Exception as exc:
            logger.error("Error processing query: %s", str(exc), exc_info=True)

            # ── Return error in response (not 500) ────────────
            return ChatQueryResponse(
                answer=(
                    f"An error occurred while processing your request: {str(exc)}\n\n"
                    "Possible causes:\n"
                    "1. LLM hallucinated the function name - review agent instruction clarity\n"
                    "2. Tool not registered - verify agent.tools list\n"
                    "3. Name mismatch - check for typos\n\n"
                    "Suggested fixes:\n"
                    "- Review agent instruction to ensure tool usage is clear\n"
                    "- Verify tool is included in agent.tools list\n"
                    "- Check for typos in function name"
                ),
                session_id=request.session_id or "",
                agent_name="",
                tool_trace=[],
                events_count=0,
                error=str(exc),
            )