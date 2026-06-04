from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

_ACTION_LOGS: list[dict] = []
_LOCK = Lock()


def record_action(action_type: str, parameters: dict, status: str, reason: str | None = None) -> dict:
    entry = {
        "action_id": str(uuid4()),
        "action_type": action_type,
        "parameters": parameters,
        "status": status,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _LOCK:
        _ACTION_LOGS.append(entry)
    return entry


def list_actions(limit: int = 100) -> list[dict]:
    with _LOCK:
        return list(reversed(_ACTION_LOGS[-limit:]))


def clear_actions() -> None:
    with _LOCK:
        _ACTION_LOGS.clear()
