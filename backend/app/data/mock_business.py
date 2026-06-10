from datetime import datetime, timezone, timedelta

# ── Dynamic Dates ─────────────────────────────────────────────────────────
_now = datetime.now(timezone.utc)
_today = _now.strftime("%Y-%m-%d")
_yesterday = (_now - timedelta(days=1)).strftime("%Y-%m-%d")
_2_days_ago = (_now - timedelta(days=2)).strftime("%Y-%m-%d")
_3_days_ago = (_now - timedelta(days=3)).strftime("%Y-%m-%d")

_today_ts = _now.strftime("%Y-%m-%dT%H:%M:%SZ")
_yesterday_ts = (_now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
_2_days_ago_ts = (_now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_3_days_ago_ts = (_now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

MOCK_ORDERS = [
    # ── Today ─────────────────────────────────────────────────────
    {"order_id": "ORD-3001", "customer_id": "CUST-001", "status": "failed_payment",
     "amount": 199.99, "created_at": _today_ts},

    # ── Yesterday ─────────────────────────────────────────────────
    {"order_id": "ORD-2001", "customer_id": "CUST-001", "status": "failed_payment",
     "amount": 129.99, "created_at": _yesterday_ts},

    {"order_id": "ORD-2002", "customer_id": "CUST-002", "status": "failed_payment",
     "amount": 349.50, "created_at": _yesterday_ts},

    {"order_id": "ORD-2003", "customer_id": "CUST-003", "status": "completed",
     "amount": 45.00, "created_at": _yesterday_ts},

    # ── 2 days ago ────────────────────────────────────────────────
    {"order_id": "ORD-1001", "customer_id": "CUST-001", "status": "completed",
     "amount": 259.00, "created_at": _2_days_ago_ts},

    {"order_id": "ORD-1002", "customer_id": "CUST-002", "status": "completed",
     "amount": 89.00, "created_at": _2_days_ago_ts},

    # ── 3 days ago ────────────────────────────────────────────────
    {"order_id": "ORD-0501", "customer_id": "CUST-001", "status": "completed",
     "amount": 175.00, "created_at": _3_days_ago_ts},

    {"order_id": "ORD-0502", "customer_id": "CUST-003", "status": "completed",
     "amount": 59.00, "created_at": _3_days_ago_ts},
]

MOCK_TRANSACTIONS = [
    # ── Today ─────────────────────────────────────────────────────
    {"transaction_id": "TX-5001", "customer_id": "CUST-001", "status": "declined",
     "amount": 199.99, "date": _today, "reason": "authorization_timeout"},

    # ── Yesterday ─────────────────────────────────────────────────
    {"transaction_id": "TX-4001", "customer_id": "CUST-001", "status": "declined",
     "amount": 129.99, "date": _yesterday, "reason": "authorization_timeout"},

    {"transaction_id": "TX-4002", "customer_id": "CUST-002", "status": "declined",
     "amount": 349.50, "date": _yesterday, "reason": "processor_503"},

    {"transaction_id": "TX-4003", "customer_id": "CUST-003", "status": "approved",
     "amount": 45.00, "date": _yesterday, "reason": "approved"},

    # ── 2 days ago ────────────────────────────────────────────────
    {"transaction_id": "TX-3001", "customer_id": "CUST-001", "status": "approved",
     "amount": 259.00, "date": _2_days_ago, "reason": "approved"},

    {"transaction_id": "TX-3002", "customer_id": "CUST-002", "status": "approved",
     "amount": 89.00, "date": _2_days_ago, "reason": "approved"},

    {"transaction_id": "TX-3003", "customer_id": "CUST-001", "status": "declined",
     "amount": 50.00, "date": _2_days_ago, "reason": "insufficient_funds"},

    # ── 3 days ago ────────────────────────────────────────────────
    {"transaction_id": "TX-2001", "customer_id": "CUST-001", "status": "approved",
     "amount": 175.00, "date": _3_days_ago, "reason": "approved"},

    {"transaction_id": "TX-2002", "customer_id": "CUST-003", "status": "approved",
     "amount": 59.00, "date": _3_days_ago, "reason": "approved"},
]

MOCK_CUSTOMER_PROFILES = {
    "CUST-001": {
        "customer_id": "CUST-001", "name": "Avery Stone",
        "email": "avery.stone@example.com", "phone": "+1-555-0101",
        "segment": "enterprise", "open_complaints": 2,
    },
    "CUST-002": {
        "customer_id": "CUST-002", "name": "Morgan Lee",
        "email": "morgan.lee@example.com", "phone": "+1-555-0102",
        "segment": "mid_market", "open_complaints": 1,
    },
    "CUST-003": {
        "customer_id": "CUST-003", "name": "Riley Kim",
        "email": "riley.kim@example.com", "phone": "+1-555-0103",
        "segment": "smb", "open_complaints": 0,
    },
}