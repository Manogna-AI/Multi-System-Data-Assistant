from app.config import get_settings
from app.mcp_clients.observability_toolset import ObservabilityMCPToolset, ToolTrace


class ObservabilityAgent:
    name = "observability_agent"

    def __init__(self) -> None:
        settings = get_settings()
        self.toolset = ObservabilityMCPToolset(settings.observability_mcp_url)

    def answer(self, service_name: str = "payment-service") -> tuple[dict, list[ToolTrace]]:
        traces: list[ToolTrace] = []
        logs, trace = self.toolset.get_logs(service_name, "2026-06-03T00:00:00Z", "2026-06-03T23:59:59Z")
        traces.append(trace)
        metrics, trace = self.toolset.get_metrics(service_name, "error_rate", "24h")
        traces.append(trace)
        alerts, trace = self.toolset.get_alerts(service_name)
        traces.append(trace)
        return {"service_name": service_name, "logs": logs, "metrics": metrics, "alerts": alerts}, traces
