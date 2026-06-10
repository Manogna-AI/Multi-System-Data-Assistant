from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    """Dependency injection for ChatService."""
    return ChatService()


@router.post("/query", response_model=ChatQueryResponse)
async def query_chat(
    request: ChatQueryRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatQueryResponse:
    """Process a user query through the ADK agent pipeline.

    The ADK Root Agent handles:
    - Intent classification (OBSERVE | BUSINESS | ACTION | CROSS-QUERY)
    - Routing to specialized sub-agents
    - MCP tool invocation via McpToolset protocol
    - Multi-turn session context
    - Response generation via Ollama LLM

    For multi-turn conversations, pass session_id from previous response.
    For action confirmations, include "yes" or "confirm" in the query text.
    """
    return await service.handle_query(request)