"""
Chat Schemas — Pydantic request/response models for /chat/query endpoint.

Designed for the ADK-powered pipeline where:
    - The ADK agent handles intent classification internally
    - MCP tools are invoked via McpToolset (protocol-based)
    - Sessions provide multi-turn context
    - No separate LLM summarization needed
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.common import ToolTraceItem


class ChatQueryRequest(BaseModel):
    """Request model for POST /chat/query.

    The query is sent to the ADK Root Agent which handles:
    - Intent classification (OBSERVE | BUSINESS | ACTION | CROSS-QUERY)
    - Routing to the correct sub-agent(s)
    - MCP tool invocation
    - Response generation

    For multi-turn conversations, pass session_id from the previous response.
    For action confirmations, include confirmation in the query text
    (e.g., "yes, restart payment-service") — the Action Agent handles
    confirmation at the conversation level.
    """

    query: str = Field(
        min_length=1,
        max_length=2000,
        description="User's natural language query",
    )
    user_id: str = Field(
        default="default_user",
        description="Unique user identifier for session management",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for multi-turn context. "
        "If None, a new session is created.",
    )


class ChatQueryResponse(BaseModel):
    """Response model for POST /chat/query.

    Contains the agent's response and session metadata.
    The ADK agent handles all intelligence — intent classification,
    tool invocation, data synthesis — so the response is a single
    coherent answer text.
    """

    answer: str = Field(description="Agent's natural language response")
    session_id: str = Field(
        description="Session ID for multi-turn continuity. "
        "Pass this in the next request to maintain context.",
    )
    agent_name: Optional[str] = Field(
        default=None,
        description="Name of the agent that produced the final response",
    )
    events_count: int = Field(
        default=0,
        description="Number of ADK events processed during execution",
    )
    tool_trace: list[ToolTraceItem] = Field(
        default_factory=list,
        description="MCP tools invoked during execution",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed",
    )