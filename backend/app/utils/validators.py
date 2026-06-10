from datetime import datetime
import re
from app.config import get_settings
from app.utils.errors import ActionRejectedError, DomainValidationError

ALLOWED_TRANSACTION_STATUSES = {"approved", "declined", "refunded", "pending", "failed"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "critical"}
ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_RANGE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}:\d{4}-\d{2}-\d{2}$")
CUSTOMER_ID_PATTERN = re.compile(r"^CUST-[0-9]{3,}$")


def validate_service_name(service_name: str) -> str:
    service = service_name.strip().lower()
    if service not in get_settings().allowed_services:
        raise DomainValidationError(f"service_name must be one of {get_settings().allowed_services}")
    return service


def parse_iso_utc(value: str) -> datetime:
    try:
        return datetime.strptime(value, ISO_FORMAT)
    except ValueError as exc:
        raise DomainValidationError("time must use ISO UTC format YYYY-MM-DDTHH:MM:SSZ") from exc


def validate_time_range(start_time: str, end_time: str) -> tuple[datetime, datetime]:
    start = parse_iso_utc(start_time)
    end = parse_iso_utc(end_time)
    if end <= start:
        raise DomainValidationError("end_time must be after start_time")
    hours = (end - start).total_seconds() / 3600
    if hours > get_settings().max_time_window_hours:
        raise DomainValidationError(f"time window must be <= {get_settings().max_time_window_hours} hours")
    return start, end


def validate_window(window: str) -> str:
    allowed = {"1h", "6h", "12h", "24h"}
    if window not in allowed:
        raise DomainValidationError(f"window must be one of {sorted(allowed)}")
    return window


def validate_date_range(date_range: str) -> tuple[str, str]:
    if not DATE_RANGE_PATTERN.match(date_range):
        raise DomainValidationError("date_range must use YYYY-MM-DD:YYYY-MM-DD")
    start, end = date_range.split(":")
    if end < start:
        raise DomainValidationError("date_range end must be on or after start")
    return start, end


def validate_customer_id(customer_id: str) -> str:
    customer = customer_id.strip().upper()
    if not customer or not CUSTOMER_ID_PATTERN.match(customer):
        raise DomainValidationError("customer_id is mandatory and must match CUST-###")
    return customer


def validate_transaction_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized not in ALLOWED_TRANSACTION_STATUSES:
        raise DomainValidationError(f"status must be one of {sorted(ALLOWED_TRANSACTION_STATUSES)}")
    return normalized


def validate_priority(priority: str) -> str:
    normalized = priority.strip().lower()
    if normalized not in ALLOWED_PRIORITIES:
        raise ActionRejectedError(f"priority must be one of {sorted(ALLOWED_PRIORITIES)}")
    return normalized


def require_confirmation(confirm: bool) -> None:
    if confirm is not True:
        raise ActionRejectedError("confirm=True is required for all actions")


def validate_replicas(replicas: int) -> int:
    if not 1 <= replicas <= 5:
        raise ActionRejectedError("replicas must be between 1 and 5")
    return replicas
