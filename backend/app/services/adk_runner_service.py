"""
ADK Runner Service — Single runner, root agent handles everything.

Architecture:
  ChatService → AdkRunnerService → Runner(root_agent)
    → Single-domain: root transfers to sub-agent
    → Cross-domain: root calls tools directly and synthesizes
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.root_agent import root_agent
from app.config import Settings, get_settings

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
    """Structured result from an agent query execution."""
    response: str = ""
    session_id: str = ""
    agent_name: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    events_count: int = 0
    intent: str = ""


def _clean_response(text: str) -> str:
    """Remove reasoning leakage and keep only clean user-facing content."""
    if not text:
        return ""

    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    unwanted_patterns = [
        r"(?im)^we can provide answer:.*$",
        r"(?im)^we need to .*?$",
        r"(?im)^the user didn't .*?$",
        r"(?im)^according to tool usage rules.*$",
        r"(?im)^we don't have a tool.*$",
        r"(?im)^now format.*$",
        r"(?im)^analysis:.*$",
        r"(?im)^observation:.*$",
        r"(?im)^let me .*?$",
        r"(?im)^i will .*?$",
        r"(?im)^thus .*?$",
    ]

    for pattern in unwanted_patterns:
        text = re.sub(pattern, "", text).strip()

    lines = [line.rstrip() for line in text.splitlines()]
    cleaned_lines = []
    previous_blank = False

    for line in lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(line)
        previous_blank = is_blank

    text = "\n".join(cleaned_lines).strip()

    lower_text = text.lower()

    if ("please provide" in lower_text or "please specify" in lower_text) and not text.startswith("##"):
        return f"## Clarification Needed\n\n{text}"

    if "i don't have the required tools" in lower_text and not text.startswith("##"):
        return f"## Tool Limitation\n\n{text}"

    return text


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
        """Execute a user query through the ADK agent pipeline."""

        # Session management
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

        # Run agent pipeline
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

            if hasattr(event, "author") and event.author:
                agent_name = event.author

            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        current_tool = ToolCall(
                            agent_name=agent_name,
                            tool_name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                        tool_calls.append(current_tool)

                    if hasattr(part, "function_response") and part.function_response:
                        fr = part.function_response
                        if current_tool and current_tool.tool_name == fr.name:
                            current_tool.result = (
                                dict(fr.response) if fr.response else None
                            )

            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts:
                    text_parts = []
                    for part in event.content.parts:
                        if getattr(part, "text", None):
                            text_parts.append(part.text)
                    response_text = "\n".join(text_parts).strip()

        response_text = _clean_response(response_text)

        logger.info(
            "Query complete: agent=%s, tools=%d, response=%d chars",
            agent_name, len(tool_calls), len(response_text),
        )

        return QueryResult(
            response=response_text,
            session_id=sid,
            agent_name=agent_name,
            tool_calls=tool_calls,
            events_count=events_count,
        )