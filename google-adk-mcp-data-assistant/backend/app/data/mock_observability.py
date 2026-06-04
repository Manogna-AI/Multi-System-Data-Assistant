from datetime import datetime

MOCK_LOGS = [
    {"timestamp": "2026-06-03T09:05:00Z", "service_name": "payment-service", "level": "ERROR", "message": "Card authorization timeouts increased", "correlation_id": "corr-pay-101"},
    {"timestamp": "2026-06-03T09:09:00Z", "service_name": "payment-service", "level": "WARN", "message": "Retry queue latency above baseline", "correlation_id": "corr-pay-102"},
    {"timestamp": "2026-06-03T10:15:00Z", "service_name": "checkout-service", "level": "ERROR", "message": "Payment callback returned 503", "correlation_id": "corr-checkout-201"},
    {"timestamp": "2026-06-03T11:20:00Z", "service_name": "orders-service", "level": "INFO", "message": "Order ingestion operating normally", "correlation_id": "corr-orders-301"},
]

MOCK_METRICS = {
    ("payment-service", "error_rate", "24h"): {"service_name": "payment-service", "metric_name": "error_rate", "window": "24h", "value": 4.8, "unit": "percent", "baseline": 0.7},
    ("payment-service", "latency_p95_ms", "24h"): {"service_name": "payment-service", "metric_name": "latency_p95_ms", "window": "24h", "value": 2150, "unit": "ms", "baseline": 420},
    ("checkout-service", "error_rate", "24h"): {"service_name": "checkout-service", "metric_name": "error_rate", "window": "24h", "value": 2.1, "unit": "percent", "baseline": 0.5},
}

MOCK_ALERTS = [
    {"service_name": "payment-service", "severity": "critical", "title": "Payment authorization failures", "started_at": "2026-06-03T09:00:00Z", "status": "open"},
    {"service_name": "checkout-service", "severity": "high", "title": "Checkout callback degradation", "started_at": "2026-06-03T09:30:00Z", "status": "open"},
]


def in_range(timestamp: str, start: datetime, end: datetime) -> bool:
    parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return start <= parsed <= end
