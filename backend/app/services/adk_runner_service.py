"""
ADK Runner Service — Single runner, root agent handles everything.

Architecture:
  ChatService → AdkRunnerService → Runner(root_agent)
    → Single-domain: root transfers to sub-agent
    → Cross-domain: root calls tools directly and synthesizes

Output guardrails are applied after the ADK pipeline produces a raw
response. The guardrails separate thinking from the clean answer,
redact PII, and standardize short responses.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.root_agent import root_agent
from app.config import Settings, get_settings
from app.utils.guardrails import apply_output_guardrails

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single MCP tool invocation extracted from ADK events."""

    agent_name: str = ""
    tool_name: str = ""
    arguments: dict = field(default_factory=dict)
    result: Any = None


@dataclass
class QueryResult:
    """Structured result from an agent query execution.

    Attributes:
        response: Clean, user-facing answer (reasoning removed).
        thinking: Agent's internal reasoning trace (for collapsible UI).
        session_id: ADK session identifier for multi-turn continuity.
        agent_name: Name of the agent that produced the final response.
        tool_calls: List of MCP tool invocations made during execution.
        events_count: Number of ADK events processed.
        intent: Detected intent category (if applicable).
    """

    response: str = ""
    thinking: str = ""
    session_id: str = ""
    agent_name: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    events_count: int = 0
    intent: str = ""


class AdkRunnerService:
    """ADK-powered service — single Runner, root agent handles all routing."""

    APP_NAME = "multi-system-data-assistant"

    def __init__(self, settings: Settings | None = None):
        logger.info("Initializing ADK Runner Service...")
        self._settings = settings or get_settings()
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=root_agent,
            app_name=self.APP_NAME,
            session_service=self._session_service,
        )
        logger.info("ADK Runner Service initialized (single runner).")

    async def query(
        self, user_id: str, message: str, session_id: str | None = None
    ) -> QueryResult:
        """Execute a user query through the ADK agent pipeline.

        Args:
            user_id: Unique user identifier for session scoping.
            message: Cleaned user query (already passed input guardrails).
            session_id: Optional session ID for multi-turn continuity.

        Returns:
            QueryResult with clean response, thinking trace, tool calls,
            and session metadata.
        """

        # ── Session management ────────────────────────────────
        sid = session_id or str(uuid.uuid4())
        try:
            session = await self._session_service.get_session(
                app_name=self.APP_NAME, user_id=user_id, session_id=sid
            )
        except Exception:
            session = None

        if session is None:
            session = await self._session_service.create_session(
                app_name=self.APP_NAME, user_id=user_id, session_id=sid
            )
            logger.info("Created session: %s", sid)

        # ── Run agent pipeline ────────────────────────────────
        user_content = types.Content(
            role="user", parts=[types.Part.from_text(text=message)]
        )

        response_text = ""
        tool_calls: list[ToolCall] = []
        current_tool: ToolCall | None = None
        events_count = 0
        agent_name = "data_analyst_assistant"

        async for event in self._runner.run_async(
            user_id=user_id, session_id=sid, new_message=user_content
        ):
            events_count += 1

            # Track which agent is currently active
            if hasattr(event, "author") and event.author:
                agent_name = event.author

            # Extract tool calls and tool responses from event parts
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    # Tool call (agent → MCP tool)
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        current_tool = ToolCall(
                            agent_name=agent_name,
                            tool_name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                        tool_calls.append(current_tool)

                    # Tool response (MCP tool → agent)
                    if hasattr(part, "function_response") and part.function_response:
                        fr = part.function_response
                        if current_tool and current_tool.tool_name == fr.name:
                            current_tool.result = (
                                dict(fr.response) if fr.response else None
                            )

            # Capture the final response text from all text parts
            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts:
                    text_parts = []
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            text_parts.append(part.text)
                    response_text = "\n".join(text_parts).strip()

        # ── Output guardrails ─────────────────────────────────
        # Separate thinking from clean answer, redact PII,
        # standardize short responses, ensure safe fallback.
        guardrail_result = apply_output_guardrails(response_text)

        logger.info(
            "Query complete: agent=%s, tools=%d, answer=%d chars, thinking=%d chars",
            agent_name,
            len(tool_calls),
            len(guardrail_result.answer),
            len(guardrail_result.thinking),
        )

        return QueryResult(
            response=guardrail_result.answer,
            thinking=guardrail_result.thinking,
            session_id=sid,
            agent_name=agent_name,
            tool_calls=tool_calls,
            events_count=events_count,
        )