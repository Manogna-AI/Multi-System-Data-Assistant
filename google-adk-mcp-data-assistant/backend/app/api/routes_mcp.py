from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/servers")
def list_mcp_servers() -> dict:
    settings = get_settings()
    return {
        "servers": [
            {"name": "observability", "url": settings.observability_mcp_url, "tools": ["get_logs", "get_metrics", "get_alerts"], "access": "read_only"},
            {"name": "business", "url": settings.business_mcp_url, "tools": ["get_orders", "get_transactions", "get_customer_profile"], "access": "read_only_masked"},
            {"name": "action", "url": settings.action_mcp_url, "tools": ["restart_service", "create_ticket", "scale_service"], "access": "confirmed_actions_only"},
        ]
    }
