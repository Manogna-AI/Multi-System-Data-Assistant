import importlib
import importlib.util
from dataclasses import dataclass
from typing import Any

from mcp_servers import business_data_server


@dataclass(frozen=True)
class ToolTrace:
    server: str
    tool: str
    arguments: dict[str, Any]
    status: str


class BusinessMCPToolset:
    def __init__(self, url: str):
        self.url = url
        self.adk_toolset = self._build_adk_toolset(url)

    @staticmethod
    def _build_adk_toolset(url: str) -> Any | None:
        if importlib.util.find_spec("google.adk.tools.mcp_tool") is None:
            return None
        module = importlib.import_module("google.adk.tools.mcp_tool")
        manager = importlib.import_module("google.adk.tools.mcp_tool.mcp_session_manager")
        params = manager.StreamableHTTPServerParams(url=url)
        return module.McpToolset(connection_params=params)

    def get_orders(self, customer_id: str) -> tuple[list[dict], ToolTrace]:
        args = {"customer_id": customer_id}
        return business_data_server.get_orders(**args), ToolTrace("business", "get_orders", args, "success")

    def get_transactions(self, date_range: str, status: str) -> tuple[list[dict], ToolTrace]:
        args = {"date_range": date_range, "status": status}
        return business_data_server.get_transactions(**args), ToolTrace("business", "get_transactions", args, "success")

    def get_customer_profile(self, customer_id: str) -> tuple[dict, ToolTrace]:
        args = {"customer_id": customer_id}
        return business_data_server.get_customer_profile(**args), ToolTrace("business", "get_customer_profile", args, "success")
