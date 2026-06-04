from fastapi import APIRouter, Depends
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    return ChatService()


@router.post("/query", response_model=ChatQueryResponse)
async def query_chat(request: ChatQueryRequest, service: ChatService = Depends(get_chat_service)) -> ChatQueryResponse:
    return await service.handle_query(request)
