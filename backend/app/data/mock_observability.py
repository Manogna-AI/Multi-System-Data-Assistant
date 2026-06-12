"""
Observability Mock Data — Logs, Metrics, Alerts, and Service Health.

Designed to support a wide range of user queries:
  - Logs: by service, level (ERROR/WARN/INFO/DEBUG), keyword, time range
  - Metrics: error_rate, latency_p95_ms, throughput across multiple windows
  - Alerts: active, resolved, by severity, by service
  - Service health: per-service status, replica counts, uptime
  - Cross-entity correlation: alerts ↔ metrics ↔ logs

Data relationships:
  - 4 services: payment-service, checkout-service, orders-service, inventory-service
  - 15 log entries across 4 levels
  - 16 metric combinations (4 services × 3 metrics × multiple windows)
  - 7 alerts (4 active, 3 resolved)
  - 4 service health records
"""

from datetime import datetime, timezone, timedelta

# ── Dynamic Dates ─────────────────────────────────────────────────────────
_now = datetime.now(timezone.utc)
_today_ts = _now.strftime("%Y-%m-%dT%H:%M:%SZ")
_30m_ago = (_now - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
_1h_ago = (_now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
_2h_ago = (_now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_3h_ago = (_now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
_5h_ago = (_now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
_8h_ago = (_now - timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
_12h_ago = (_now - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
_yesterday_morning = (_now - timedelta(days=1, hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
_yesterday_noon = (_now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
_2_days_ago = (_now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Logs ──────────────────────────────────────────────────────────────────
# 15 log entries, 4 services, 4 levels (ERROR, WARN, INFO, DEBUG)
MOCK_LOGS = [
    # ── payment-service ───────────────────────────────────────────
    {"timestamp": _30m_ago, "service_name": "payment-service", "level": "ERROR",
     "message": "Card authorization timeout — gateway returned 504 after 30s",
     "correlation_id": "corr-pay-100"},

    {"timestamp": _1h_ago, "service_name": "payment-service", "level": "ERROR",
     "message": "Card authorization timeouts increased — gateway returned 504",
     "correlation_id": "corr-pay-101"},

    {"timestamp": _2h_ago, "service_name": "payment-service", "level": "WARN",
     "message": "Retry queue latency above baseline (3200ms vs 400ms normal)",
     "correlation_id": "corr-pay-102"},

    {"timestamp": _5h_ago, "service_name": "payment-service", "level": "ERROR",
     "message": "Database connection pool exhausted — max connections reached",
     "correlation_id": "corr-pay-103"},

    {"timestamp": _8h_ago, "service_name": "payment-service", "level": "INFO",
     "message": "Payment processor health check passed — all endpoints responding",
     "correlation_id": "corr-pay-104"},

    {"timestamp": _12h_ago, "service_name": "payment-service", "level": "DEBUG",
     "message": "Cache refresh completed — 1250 entries updated in 45ms",
     "correlation_id": "corr-pay-105"},

    # ── checkout-service ──────────────────────────────────────────
    {"timestamp": _3h_ago, "service_name": "checkout-service", "level": "ERROR",
     "message": "Payment callback returned 503 — upstream payment-service degraded",
     "correlation_id": "corr-checkout-201"},

    {"timestamp": _yesterday_noon, "service_name": "checkout-service", "level": "WARN",
     "message": "Checkout latency elevated — p95 at 1800ms",
     "correlation_id": "corr-checkout-202"},

    {"timestamp": _8h_ago, "service_name": "checkout-service", "level": "INFO",
     "message": "Cart validation service operating normally — 0 errors in last hour",
     "correlation_id": "corr-checkout-203"},

    # ── orders-service ────────────────────────────────────────────
    {"timestamp": _5h_ago, "service_name": "orders-service", "level": "INFO",
     "message": "Order ingestion operating normally — processing 85 orders/min",
     "correlation_id": "corr-orders-301"},

    {"timestamp": _yesterday_morning, "service_name": "orders-service", "level": "WARN",
     "message": "Order queue depth increasing — 450 pending vs 120 baseline",
     "correlation_id": "corr-orders-302"},

    {"timestamp": _12h_ago, "service_name": "orders-service", "level": "DEBUG",
     "message": "Database index rebuild completed — query performance improved 15%",
     "correlation_id": "corr-orders-303"},

    # ── inventory-service ─────────────────────────────────────────
    {"timestamp": _2h_ago, "service_name": "inventory-service", "level": "WARN",
     "message": "Stock sync delay detected — 3 items pending update for 45 minutes",
     "correlation_id": "corr-inv-401"},

    {"timestamp": _8h_ago, "service_name": "inventory-service", "level": "INFO",
     "message": "Inventory reconciliation completed — 12,450 SKUs verified",
     "correlation_id": "corr-inv-402"},

    {"timestamp": _yesterday_morning, "service_name": "inventory-service", "level": "ERROR",
     "message": "Failed to sync with warehouse API — connection refused",
     "correlation_id": "corr-inv-403"},
]


# ── Metrics ───────────────────────────────────────────────────────────────
# 4 services × 3 metrics × multiple windows
# Metrics: error_rate (%), latency_p95_ms (ms), throughput (req/min)
MOCK_METRICS = {
    # ── payment-service ───────────────────────────────────────────
    ("payment-service", "error_rate", "1h"):
        {"service_name": "payment-service", "metric_name": "error_rate",
         "window": "1h", "value": 8.2, "unit": "percent", "baseline": 0.7},

    ("payment-service", "error_rate", "6h"):
        {"service_name": "payment-service", "metric_name": "error_rate",
         "window": "6h", "value": 5.5, "unit": "percent", "baseline": 0.7},

    ("payment-service", "error_rate", "12h"):
        {"service_name": "payment-service", "metric_name": "error_rate",
         "window": "12h", "value": 5.0, "unit": "percent", "baseline": 0.7},

    ("payment-service", "error_rate", "24h"):
        {"service_name": "payment-service", "metric_name": "error_rate",
         "window": "24h", "value": 4.8, "unit": "percent", "baseline": 0.7},

    ("payment-service", "latency_p95_ms", "1h"):
        {"service_name": "payment-service", "metric_name": "latency_p95_ms",
         "window": "1h", "value": 2800, "unit": "ms", "baseline": 420},

    ("payment-service", "latency_p95_ms", "24h"):
        {"service_name": "payment-service", "metric_name": "latency_p95_ms",
         "window": "24h", "value": 2150, "unit": "ms", "baseline": 420},

    ("payment-service", "throughput", "1h"):
        {"service_name": "payment-service", "metric_name": "throughput",
         "window": "1h", "value": 980, "unit": "req/min", "baseline": 3400},

    ("payment-service", "throughput", "24h"):
        {"service_name": "payment-service", "metric_name": "throughput",
         "window": "24h", "value": 1250, "unit": "req/min", "baseline": 3400},

    # ── checkout-service ──────────────────────────────────────────
    ("checkout-service", "error_rate", "1h"):
        {"service_name": "checkout-service", "metric_name": "error_rate",
         "window": "1h", "value": 3.1, "unit": "percent", "baseline": 0.5},

    ("checkout-service", "error_rate", "24h"):
        {"service_name": "checkout-service", "metric_name": "error_rate",
         "window": "24h", "value": 2.1, "unit": "percent", "baseline": 0.5},

    ("checkout-service", "latency_p95_ms", "24h"):
        {"service_name": "checkout-service", "metric_name": "latency_p95_ms",
         "window": "24h", "value": 1800, "unit": "ms", "baseline": 350},

    ("checkout-service", "throughput", "24h"):
        {"service_name": "checkout-service", "metric_name": "throughput",
         "window": "24h", "value": 2100, "unit": "req/min", "baseline": 2800},

    # ── orders-service ────────────────────────────────────────────
    ("orders-service", "error_rate", "24h"):
        {"service_name": "orders-service", "metric_name": "error_rate",
         "window": "24h", "value": 0.1, "unit": "percent", "baseline": 0.2},

    ("orders-service", "latency_p95_ms", "24h"):
        {"service_name": "orders-service", "metric_name": "latency_p95_ms",
         "window": "24h", "value": 180, "unit": "ms", "baseline": 200},

    ("orders-service", "throughput", "24h"):
        {"service_name": "orders-service", "metric_name": "throughput",
         "window": "24h", "value": 850, "unit": "req/min", "baseline": 900},

    # ── inventory-service ─────────────────────────────────────────
    ("inventory-service", "error_rate", "24h"):
        {"service_name": "inventory-service", "metric_name": "error_rate",
         "window": "24h", "value": 1.2, "unit": "percent", "baseline": 0.3},

    ("inventory-service", "latency_p95_ms", "24h"):
        {"service_name": "inventory-service", "metric_name": "latency_p95_ms",
         "window": "24h", "value": 520, "unit": "ms", "baseline": 300},

    ("inventory-service", "throughput", "24h"):
        {"service_name": "inventory-service", "metric_name": "throughput",
         "window": "24h", "value": 450, "unit": "req/min", "baseline": 600},
}


# ── Alerts ────────────────────────────────────────────────────────────────
# 7 alerts: 4 active (open), 3 resolved
MOCK_ALERTS = [
    # ── Active alerts ─────────────────────────────────────────────
    {"alert_id": "ALT-001", "service_name": "payment-service", "severity": "critical",
     "title": "Payment authorization failure rate >4%",
     "started_at": _3h_ago, "status": "open",
     "description": "Error rate exceeded critical threshold of 4%. Current: 8.2%"},

    {"alert_id": "ALT-002", "service_name": "payment-service", "severity": "high",
     "title": "Payment-service latency p95 >2000ms",
     "started_at": _5h_ago, "status": "open",
     "description": "P95 latency at 2150ms, baseline is 420ms"},

    {"alert_id": "ALT-003", "service_name": "checkout-service", "severity": "high",
     "title": "Checkout callback degradation — upstream 503s",
     "started_at": _2h_ago, "status": "open",
     "description": "Checkout receiving 503 from payment-service callbacks"},

    {"alert_id": "ALT-004", "service_name": "inventory-service", "severity": "medium",
     "title": "Inventory sync delay exceeding 30 minutes",
     "started_at": _2h_ago, "status": "open",
     "description": "Stock sync with warehouse API delayed beyond threshold"},

    # ── Resolved alerts ───────────────────────────────────────────
    {"alert_id": "ALT-005", "service_name": "payment-service", "severity": "high",
     "title": "Database connection pool near exhaustion",
     "started_at": _12h_ago, "resolved_at": _8h_ago, "status": "resolved",
     "description": "Connection pool recovered after autoscaling kicked in"},

    {"alert_id": "ALT-006", "service_name": "orders-service", "severity": "medium",
     "title": "Order queue depth above baseline",
     "started_at": _yesterday_morning, "resolved_at": _yesterday_noon, "status": "resolved",
     "description": "Queue depth normalized after processing backlog cleared"},

    {"alert_id": "ALT-007", "service_name": "inventory-service", "severity": "high",
     "title": "Warehouse API connection refused",
     "started_at": _yesterday_morning, "resolved_at": _12h_ago, "status": "resolved",
     "description": "Warehouse API endpoint restored after provider maintenance"},
]


# ── Service Health ────────────────────────────────────────────────────────
# Per-service status, replica counts, uptime
MOCK_SERVICE_HEALTH = {
    "payment-service": {
        "service_name": "payment-service",
        "status": "degraded",
        "current_replicas": 3,
        "max_replicas": 5,
        "uptime_hours": 72.5,
        "last_restart": _2_days_ago,
        "active_alert_count": 2,
        "maintenance_mode": False,
    },
    "checkout-service": {
        "service_name": "checkout-service",
        "status": "degraded",
        "current_replicas": 2,
        "max_replicas": 5,
        "uptime_hours": 168.0,
        "last_restart": (_now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "active_alert_count": 1,
        "maintenance_mode": False,
    },
    "orders-service": {
        "service_name": "orders-service",
        "status": "healthy",
        "current_replicas": 2,
        "max_replicas": 5,
        "uptime_hours": 336.0,
        "last_restart": (_now - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "active_alert_count": 0,
        "maintenance_mode": False,
    },
    "inventory-service": {
        "service_name": "inventory-service",
        "status": "degraded",
        "current_replicas": 1,
        "max_replicas": 3,
        "uptime_hours": 48.0,
        "last_restart": _2_days_ago,
        "active_alert_count": 1,
        "maintenance_mode": False,
    },
}


def in_range(timestamp: str, start: datetime, end: datetime) -> bool:
    """Check if a timestamp string falls within a datetime range.

    Args:
        timestamp: ISO UTC timestamp string.
        start: Range start datetime.
        end: Range end datetime.

    Returns:
        True if timestamp is within [start, end].
    """
    parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return start <= parsed <= end