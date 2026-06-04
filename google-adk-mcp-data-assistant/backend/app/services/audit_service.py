from app.data.action_log_store import list_actions


class AuditService:
    def list_action_audit(self) -> list[dict]:
        return list_actions()
