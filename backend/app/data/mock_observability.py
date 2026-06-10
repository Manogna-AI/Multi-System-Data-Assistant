from datetime import datetime, timezone, timedelta

# ── Dynamic Dates ─────────────────────────────────────────────────────────
# Generate dates relative to NOW so queries for "today" and "yesterday"
# always return data regardless of when the app is running.
_now = datetime.now(timezone.utc)
_today = _now.strftime("%Y-%m-%dT%H:%M:%SZ")
_1h_ago = (_now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
_2h_ago = (_now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_3h_ago = (_now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
_5h_ago = (_now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
_yesterday_morning = (_now - timedelta(days=1, hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
_yesterday_noon = (_now - timedelta(days=1, hours=0)).strftime("%Y-%m-%dT%H:%M:%SZ")

MOCK_LOGS = [
    # ── Today's logs ──────────────────────────────────────────────
    {"timestamp": _1h_ago, "service_name": "payment-service", "level": "ERROR",
     "message": "Card authorization timeouts increased — gateway returned 504",
     "correlation_id": "corr-pay-101"},

    {"timestamp": _2h_ago, "service_name": "payment-service", "level": "WARN",
     "message": "Retry queue latency above baseline (3200ms vs 400ms normal)",
     "correlation_id": "corr-pay-102"},

    {"timestamp": _3h_ago, "service_name": "checkout-service", "level": "ERROR",
     "message": "Payment callback returned 503 — upstream payment-service degraded",
     "correlation_id": "corr-checkout-201"},

    {"timestamp": _5h_ago, "service_name": "payment-service", "level": "ERROR",
     "message": "Database connection pool exhausted — max connections reached",
     "correlation_id": "corr-pay-103"},

    {"timestamp": _5h_ago, "service_name": "orders-service", "level": "INFO",
     "message": "Order ingestion operating normally",
     "correlation_id": "corr-orders-301"},

    # ── Yesterday's logs ──────────────────────────────────────────
    {"timestamp": _yesterday_morning, "service_name": "payment-service", "level": "ERROR",
     "message": "Intermittent timeout on card processor API",
     "correlation_id": "corr-pay-200"},

    {"timestamp": _yesterday_noon, "service_name": "checkout-service", "level": "WARN",
     "message": "Checkout latency elevated — p95 at 1800ms",
     "correlation_id": "corr-checkout-202"},
]

MOCK_METRICS = {
    ("payment-service", "error_rate", "24h"):
        {"service_name": "payment-service", "metric_name": "error_rate",
         "window": "24h", "value": 4.8, "unit": "percent", "baseline": 0.7},

    ("payment-service", "latency_p95_ms", "24h"):
        {"service_name": "payment-service", "metric_name": "latency_p95_ms",
         "window": "24h", "value": 2150, "unit": "ms", "baseline": 420},

    ("payment-service", "error_rate", "1h"):
        {"service_name": "payment-service", "metric_name": "error_rate",
         "window": "1h", "value": 8.2, "unit": "percent", "baseline": 0.7},

    ("payment-service", "throughput", "24h"):
        {"service_name": "payment-service", "metric_name": "throughput",
         "window": "24h", "value": 1250, "unit": "req/min", "baseline": 3400},

    ("checkout-service", "error_rate", "24h"):
        {"service_name": "checkout-service", "metric_name": "error_rate",
         "window": "24h", "value": 2.1, "unit": "percent", "baseline": 0.5},

    ("checkout-service", "latency_p95_ms", "24h"):
        {"service_name": "checkout-service", "metric_name": "latency_p95_ms",
         "window": "24h", "value": 1800, "unit": "ms", "baseline": 350},

    ("orders-service", "error_rate", "24h"):
        {"service_name": "orders-service", "metric_name": "error_rate",
         "window": "24h", "value": 0.1, "unit": "percent", "baseline": 0.2},
}

MOCK_ALERTS = [
    {"service_name": "payment-service", "severity": "critical",
     "title": "Payment authorization failure rate >4%",
     "started_at": _3h_ago, "status": "open"},

    {"service_name": "payment-service", "severity": "high",
     "title": "Payment-service latency p95 >2000ms",
     "started_at": _5h_ago, "status": "open"},

    {"service_name": "checkout-service", "severity": "high",
     "title": "Checkout callback degradation — upstream 503s",
     "started_at": _2h_ago, "status": "open"},
]


def in_range(timestamp: str, start: datetime, end: datetime) -> bool:
    parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return start <= parsed <= end