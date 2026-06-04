from app.config import get_settings
from app.mcp_clients.business_toolset import BusinessMCPToolset, ToolTrace


class BusinessDataAgent:
    name = "business_data_agent"

    def __init__(self) -> None:
        self.toolset = BusinessMCPToolset(get_settings().business_mcp_url)

    def answer(self, customer_id: str = "CUST-001") -> tuple[dict, list[ToolTrace]]:
        traces: list[ToolTrace] = []
        declined, trace = self.toolset.get_transactions("2026-06-03:2026-06-03", "declined")
        traces.append(trace)
        orders, trace = self.toolset.get_orders(customer_id)
        traces.append(trace)
        profile, trace = self.toolset.get_customer_profile(customer_id)
        traces.append(trace)
        return {"customer_id": customer_id, "declined_transactions": declined, "orders": orders, "customer_profile": profile}, traces
