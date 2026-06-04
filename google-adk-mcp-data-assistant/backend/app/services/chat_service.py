from app.agents.root_agent import RootAgent
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.llm_service import LLMService
from app.services.response_builder import ResponseBuilder


class ChatService:
    def __init__(self) -> None:
        self.root_agent = RootAgent()
        self.llm_service = LLMService()

    async def handle_query(self, request: ChatQueryRequest) -> ChatQueryResponse:
        intent, data, traces = self.root_agent.run(request.query, request.confirm_action)
        answer = await self.llm_service.summarize(request.query, data)
        return ResponseBuilder.build(intent, data, traces, answer, request.confirm_action)
