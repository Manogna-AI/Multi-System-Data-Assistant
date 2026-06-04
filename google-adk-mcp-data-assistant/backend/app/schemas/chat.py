from pydantic import BaseModel, Field
from app.schemas.common import ToolTraceItem


class ChatQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    confirm_action: bool = False


class ActionConfirmationStatus(BaseModel):
    required: bool
    confirmed: bool
    status: str | None = None
    message: str | None = None


class ChatQueryResponse(BaseModel):
    answer: str
    intent: str
    tool_trace: list[ToolTraceItem]
    action_confirmation: ActionConfirmationStatus
    data: dict
