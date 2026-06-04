from app.config import get_settings
from app.mcp_clients.action_toolset import ActionMCPToolset, ToolTrace


class ActionAgent:
    name = "action_agent"

    def __init__(self) -> None:
        self.toolset = ActionMCPToolset(get_settings().action_mcp_url)

    def answer(self, query: str, service_name: str = "payment-service", confirm: bool = False) -> tuple[dict, list[ToolTrace]]:
        q = query.lower()
        if "scale" in q:
            result, trace = self.toolset.scale_service(service_name, 2, confirm)
        elif "ticket" in q:
            result, trace = self.toolset.create_ticket("Customer impact investigation", query, "high", confirm)
        else:
            result, trace = self.toolset.restart_service(service_name, confirm)
        return {"action_result": result}, [trace]
