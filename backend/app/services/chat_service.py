"""
Chat Service — FastAPI integration layer for the ADK-powered assistant.

This service bridges the FastAPI routes with the ADK Runner Service.
It handles:
  - Input guardrails (prompt-injection, empty/long query rejection)
  - Request validation and transformation
  - Session management (user_id, session_id)
  - Delegating to AdkRunnerService for agent execution
  - Mapping ADK ToolCall → ToolTraceItem for the frontend
  - Error guardrails (safe user-facing error messages)
  - Formatting ADK QueryResult → ChatQueryResponse for the frontend

Architecture Mapping:
  routes_chat.py → ChatService → AdkRunnerService → ADK Runner
    → Root Agent → Sub-agents → McpToolset → MCP Servers
"""

from __future__ import annotations

import logging
from typing import Optional

from app.config import get_settings
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.schemas.common import ToolTraceItem
from app.services.adk_runner_service import AdkRunnerService
from app.utils.guardrails import (
    apply_input_guardrails,
    map_exception_to_user_message,
)

logger = logging.getLogger(__name__)

# ── Singleton ADK Runner Service ──────────────────────────────────────────
# Created once and reused across all requests.
# The Runner holds the root agent and session service.

_adk_service: Optional[AdkRunnerService] = None


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
      1. Run input guardrails on the raw user query
      2. Accept ChatQueryRequest from the route handler
      3. Delegate to AdkRunnerService for agent execution
      4. Map ADK ToolCall objects → ToolTraceItem Pydantic models
      5. Return ChatQueryResponse to the route handler
      6. Map exceptions to safe user-facing error messages

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
            ChatQueryResponse with answer, thinking, tool_trace, session_id,
            agent_name.
        """
        logger.info("Processing chat query: '%s'", request.query[:80])

        try:
            # ── Input Guardrails ──────────────────────────────
            # Checks: empty, too long, prompt-injection.
            # Runs BEFORE the query reaches the ADK agent layer.
            decision = apply_input_guardrails(request.query)
            if not decision.allowed:
                logger.warning(
                    "Input guardrail blocked query: reason=%s",
                    decision.reason,
                )
                return ChatQueryResponse(
                    answer=decision.message,
                    thinking="",
                    session_id=request.session_id or "",
                    agent_name="",
                    tool_trace=[],
                    events_count=0,
                    error=decision.reason,
                )

            # ── Execute via ADK Runner Service ────────────────
            # Uses the cleaned text from input guardrails, not
            # the raw query, to ensure normalized input.
            result = await self.adk_service.query(
                user_id=request.user_id or "default_user",
                message=decision.cleaned_text,
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
            # response = clean answer (reasoning already removed)
            # thinking = separated reasoning trace (for collapsible UI)
            answer = result.response or "No response from agent."
            thinking = result.thinking or ""

            logger.info(
                "Chat response: agent=%s, tools=%d, answer_len=%d, thinking_len=%d",
                result.agent_name,
                len(tool_trace),
                len(answer),
                len(thinking),
            )

            return ChatQueryResponse(
                answer=answer,
                thinking=thinking,
                session_id=result.session_id,
                agent_name=result.agent_name,
                tool_trace=tool_trace,
                events_count=result.events_count,
                error=None,
            )

        except Exception as exc:
            logger.error("Error processing query: %s", str(exc), exc_info=True)

            # ── Error Guardrail ───────────────────────────────
            # Converts raw exceptions into short, safe, user-facing
            # messages. No stack traces or internal paths are exposed.
            safe_answer = map_exception_to_user_message(exc)

            return ChatQueryResponse(
                answer=safe_answer,
                thinking="",
                session_id=request.session_id or "",
                agent_name="",
                tool_trace=[],
                events_count=0,
                error=str(exc),
            )