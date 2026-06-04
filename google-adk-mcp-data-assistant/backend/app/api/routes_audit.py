from fastapi import APIRouter, Depends
from app.schemas.audit import AuditActionsResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_service() -> AuditService:
    return AuditService()


@router.get("/actions", response_model=AuditActionsResponse)
def audit_actions(service: AuditService = Depends(get_audit_service)) -> AuditActionsResponse:
    return AuditActionsResponse(actions=service.list_action_audit())
