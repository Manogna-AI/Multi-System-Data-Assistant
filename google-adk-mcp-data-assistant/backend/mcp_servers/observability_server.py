import importlib
import importlib.util


def build_mcp(name: str):
    if importlib.util.find_spec("fastmcp") is None:
        class LocalFastMCP:
            def __init__(self, server_name: str):
                self.name = server_name
            def tool(self):
                def decorator(func):
                    return func
                return decorator
            def run(self, *_, **__):
                return None
        return LocalFastMCP(name)
    return importlib.import_module("fastmcp").FastMCP(name)

from app.config import get_settings
from app.data.mock_observability import MOCK_ALERTS, MOCK_LOGS, MOCK_METRICS, in_range
from app.utils.validators import validate_service_name, validate_time_range, validate_window

mcp = build_mcp("observability-server")


@mcp.tool()
def get_logs(service_name: str, start_time: str, end_time: str) -> list[dict]:
    service = validate_service_name(service_name)
    start, end = validate_time_range(start_time, end_time)
    logs = [log for log in MOCK_LOGS if log["service_name"] == service and in_range(log["timestamp"], start, end)]
    return logs[: get_settings().max_log_results]


@mcp.tool()
def get_metrics(service_name: str, metric_name: str, window: str) -> dict:
    service = validate_service_name(service_name)
    valid_window = validate_window(window)
    metric = MOCK_METRICS.get((service, metric_name, valid_window))
    if metric is None:
        return {"service_name": service, "metric_name": metric_name, "window": valid_window, "value": None, "unit": None, "baseline": None}
    return dict(metric)


@mcp.tool()
def get_alerts(service_name: str) -> list[dict]:
    service = validate_service_name(service_name)
    return [dict(alert) for alert in MOCK_ALERTS if alert["service_name"] == service][:25]


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001, path="/mcp")
