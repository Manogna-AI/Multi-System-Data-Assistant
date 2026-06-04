import importlib
import importlib.util
from dataclasses import dataclass
from typing import Any

from mcp_servers import observability_server


@dataclass(frozen=True)
class ToolTrace:
    server: str
    tool: str
    arguments: dict[str, Any]
    status: str


class ObservabilityMCPToolset:
    """ADK-compatible MCP toolset wrapper for observability tools.

    The optional `adk_toolset` property demonstrates the official ADK pattern:
    `google.adk.tools.mcp_tool.McpToolset` with streamable HTTP server params.
    Runtime orchestration uses the same typed MCP tool surface and never reads mock
    data directly from agents.
    """

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

    def get_logs(self, service_name: str, start_time: str, end_time: str) -> tuple[list[dict], ToolTrace]:
        args = {"service_name": service_name, "start_time": start_time, "end_time": end_time}
        return observability_server.get_logs(**args), ToolTrace("observability", "get_logs", args, "success")

    def get_metrics(self, service_name: str, metric_name: str, window: str) -> tuple[dict, ToolTrace]:
        args = {"service_name": service_name, "metric_name": metric_name, "window": window}
        return observability_server.get_metrics(**args), ToolTrace("observability", "get_metrics", args, "success")

    def get_alerts(self, service_name: str) -> tuple[list[dict], ToolTrace]:
        args = {"service_name": service_name}
        return observability_server.get_alerts(**args), ToolTrace("observability", "get_alerts", args, "success")
