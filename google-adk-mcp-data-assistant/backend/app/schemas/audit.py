from pydantic import BaseModel


class AuditAction(BaseModel):
    action_id: str
    action_type: str
    parameters: dict
    status: str
    reason: str | None = None
    created_at: str


class AuditActionsResponse(BaseModel):
    actions: list[AuditAction]
