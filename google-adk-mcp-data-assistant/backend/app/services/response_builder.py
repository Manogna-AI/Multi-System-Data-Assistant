from app.agents.intent_classifier import IntentResult
from app.schemas.chat import ActionConfirmationStatus, ChatQueryResponse
from app.schemas.common import ToolTraceItem


class ResponseBuilder:
    @staticmethod
    def build(intent: IntentResult, data: dict, traces: list, answer: str, confirm_action: bool) -> ChatQueryResponse:
        action_result = data.get("action", {}).get("action_result")
        action_status = None
        action_message = None
        if isinstance(action_result, dict):
            action_status = action_result.get("status")
            action_message = action_result.get("message") or action_result.get("reason")
            if action_status is None and "action" in action_result:
                action_status = action_result.get("action", {}).get("status")
                action_message = action_result.get("message")
        return ChatQueryResponse(
            answer=answer,
            intent=intent.category.value,
            tool_trace=[ToolTraceItem(server=t.server, tool=t.tool, arguments=t.arguments, status=t.status) for t in traces],
            action_confirmation=ActionConfirmationStatus(required=intent.requires_confirmation, confirmed=confirm_action, status=action_status, message=action_message),
            data=data,
        )
