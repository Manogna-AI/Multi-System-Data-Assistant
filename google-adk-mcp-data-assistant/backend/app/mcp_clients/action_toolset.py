import importlib
import importlib.util
from dataclasses import dataclass
from typing import Any

from mcp_servers import action_server


@dataclass(frozen=True)
class ToolTrace:
    server: str
    tool: str
    arguments: dict[str, Any]
    status: str


class ActionMCPToolset:
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

    def restart_service(self, service_name: str, confirm: bool) -> tuple[dict, ToolTrace]:
        args = {"service_name": service_name, "confirm": confirm}
        return action_server.restart_service(**args), ToolTrace("action", "restart_service", args, "success")

    def create_ticket(self, title: str, description: str, priority: str, confirm: bool) -> tuple[dict, ToolTrace]:
        args = {"title": title, "description": description, "priority": priority, "confirm": confirm}
        return action_server.create_ticket(**args), ToolTrace("action", "create_ticket", args, "success")

    def scale_service(self, service_name: str, replicas: int, confirm: bool) -> tuple[dict, ToolTrace]:
        args = {"service_name": service_name, "replicas": replicas, "confirm": confirm}
        return action_server.scale_service(**args), ToolTrace("action", "scale_service", args, "success")
