"""
Common Schemas — Shared Pydantic models used across the application.
"""

from __future__ import annotations

from pydantic import BaseModel


class ToolTraceItem(BaseModel):
    """Represents a single MCP tool call made by an agent."""

    agent: str
    tool: str
    arguments: dict
    result_summary: str

class HealthResponse(BaseModel):
    """Response model for GET /health endpoint."""

    status: str
    service: str
    version: str