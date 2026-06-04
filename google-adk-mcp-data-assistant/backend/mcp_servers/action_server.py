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

from app.data.action_log_store import record_action
from app.utils.validators import require_confirmation, validate_priority, validate_replicas, validate_service_name

mcp = build_mcp("action-server")


def _reject(action_type: str, parameters: dict, reason: str) -> dict:
    return record_action(action_type=action_type, parameters=parameters, status="rejected", reason=reason)


@mcp.tool()
def restart_service(service_name: str, confirm: bool) -> dict:
    params = {"service_name": service_name, "confirm": confirm}
    try:
        require_confirmation(confirm)
        service = validate_service_name(service_name)
    except ValueError as exc:
        return _reject("restart_service", params, str(exc))
    entry = record_action("restart_service", {"service_name": service, "confirm": confirm}, "accepted", "restart scheduled safely")
    return {"status": "accepted", "message": f"Restart scheduled for {service}", "action": entry}


@mcp.tool()
def create_ticket(title: str, description: str, priority: str, confirm: bool) -> dict:
    params = {"title": title, "description": description, "priority": priority, "confirm": confirm}
    try:
        require_confirmation(confirm)
        valid_priority = validate_priority(priority)
        if not title.strip() or not description.strip():
            raise ValueError("title and description are required")
    except ValueError as exc:
        return _reject("create_ticket", params, str(exc))
    entry = record_action("create_ticket", {"title": title.strip(), "priority": valid_priority, "confirm": confirm}, "accepted", "ticket created")
    return {"status": "accepted", "message": "Ticket created", "action": entry}


@mcp.tool()
def scale_service(service_name: str, replicas: int, confirm: bool) -> dict:
    params = {"service_name": service_name, "replicas": replicas, "confirm": confirm}
    try:
        require_confirmation(confirm)
        service = validate_service_name(service_name)
        safe_replicas = validate_replicas(replicas)
    except ValueError as exc:
        return _reject("scale_service", params, str(exc))
    entry = record_action("scale_service", {"service_name": service, "replicas": safe_replicas, "confirm": confirm}, "accepted", "scale scheduled safely")
    return {"status": "accepted", "message": f"Scale scheduled for {service} to {safe_replicas} replicas", "action": entry}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8003, path="/mcp")
