"""
Business Mock Data — Customers, Orders, and Transactions.

Designed to support a wide range of user queries:
  - Customer lookup, listing, search, segment filtering
  - Order filtering by customer, amount, status, date
  - Transaction filtering by customer, status, amount, date
  - Aggregation queries: revenue, counts, rates, averages
  - Cross-entity correlation: customer → orders → transactions
  - Edge cases: no-match amounts, empty results, boundary values

Data relationships:
  - 6 customers (CUST-001 to CUST-006)
  - 20 orders across 4 days with 6 statuses
  - 20 transactions across 4 days with 5 statuses
  - Amounts range from 19.99 to 899.00
  - Deliberate correlation: failed_payment orders ↔ declined transactions
"""

from datetime import datetime, timezone, timedelta

# ── Dynamic Dates ─────────────────────────────────────────────────────────
_now = datetime.now(timezone.utc)
_today = _now.strftime("%Y-%m-%d")
_yesterday = (_now - timedelta(days=1)).strftime("%Y-%m-%d")
_2_days_ago = (_now - timedelta(days=2)).strftime("%Y-%m-%d")
_3_days_ago = (_now - timedelta(days=3)).strftime("%Y-%m-%d")

_today_ts = _now.strftime("%Y-%m-%dT%H:%M:%SZ")
_today_morning_ts = (_now.replace(hour=9, minute=0, second=0)).strftime("%Y-%m-%dT%H:%M:%SZ")
_yesterday_ts = (_now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
_yesterday_morning_ts = (_now - timedelta(days=1, hours=-9)).strftime("%Y-%m-%dT%H:%M:%SZ")
_2_days_ago_ts = (_now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
_3_days_ago_ts = (_now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Customer Profiles ─────────────────────────────────────────────────────
# 6 customers across 3 segments with varying complaint counts
MOCK_CUSTOMER_PROFILES = {
    "CUST-001": {
        "customer_id": "CUST-001",
        "name": "Avery Stone",
        "email": "avery.stone@example.com",
        "phone": "+1-555-0101",
        "segment": "enterprise",
        "status": "active",
        "open_complaints": 2,
        "joined_date": "2024-03-15",
    },
    "CUST-002": {
        "customer_id": "CUST-002",
        "name": "Morgan Lee",
        "email": "morgan.lee@example.com",
        "phone": "+1-555-0102",
        "segment": "mid_market",
        "status": "active",
        "open_complaints": 1,
        "joined_date": "2024-06-22",
    },
    "CUST-003": {
        "customer_id": "CUST-003",
        "name": "Riley Kim",
        "email": "riley.kim@example.com",
        "phone": "+1-555-0103",
        "segment": "smb",
        "status": "active",
        "open_complaints": 0,
        "joined_date": "2025-01-10",
    },
    "CUST-004": {
        "customer_id": "CUST-004",
        "name": "Jordan Patel",
        "email": "jordan.patel@example.com",
        "phone": "+1-555-0104",
        "segment": "enterprise",
        "status": "active",
        "open_complaints": 3,
        "joined_date": "2023-11-05",
    },
    "CUST-005": {
        "customer_id": "CUST-005",
        "name": "Taylor Brooks",
        "email": "taylor.brooks@example.com",
        "phone": "+1-555-0105",
        "segment": "mid_market",
        "status": "inactive",
        "open_complaints": 0,
        "joined_date": "2024-09-18",
    },
    "CUST-006": {
        "customer_id": "CUST-006",
        "name": "Casey Nguyen",
        "email": "casey.nguyen@example.com",
        "phone": "+1-555-0106",
        "segment": "smb",
        "status": "active",
        "open_complaints": 1,
        "joined_date": "2025-04-01",
    },
}


# ── Orders ────────────────────────────────────────────────────────────────
# 20 orders across 4 days, 6 statuses, amounts from 19.99 to 899.00
# Statuses: completed, pending, shipped, cancelled, failed_payment, returned
MOCK_ORDERS = [
    # ── Today ─────────────────────────────────────────────────────
    {"order_id": "ORD-3001", "customer_id": "CUST-001", "status": "failed_payment",
     "amount": 199.99, "created_at": _today_ts},

    {"order_id": "ORD-3002", "customer_id": "CUST-004", "status": "pending",
     "amount": 450.00, "created_at": _today_ts},

    {"order_id": "ORD-3003", "customer_id": "CUST-006", "status": "pending",
     "amount": 89.50, "created_at": _today_morning_ts},

    {"order_id": "ORD-3004", "customer_id": "CUST-002", "status": "failed_payment",
     "amount": 599.00, "created_at": _today_ts},

    {"order_id": "ORD-3005", "customer_id": "CUST-003", "status": "completed",
     "amount": 35.00, "created_at": _today_morning_ts},

    # ── Yesterday ─────────────────────────────────────────────────
    {"order_id": "ORD-2001", "customer_id": "CUST-001", "status": "failed_payment",
     "amount": 129.99, "created_at": _yesterday_ts},

    {"order_id": "ORD-2002", "customer_id": "CUST-002", "status": "failed_payment",
     "amount": 349.50, "created_at": _yesterday_ts},

    {"order_id": "ORD-2003", "customer_id": "CUST-003", "status": "completed",
     "amount": 45.00, "created_at": _yesterday_ts},

    {"order_id": "ORD-2004", "customer_id": "CUST-004", "status": "shipped",
     "amount": 899.00, "created_at": _yesterday_morning_ts},

    {"order_id": "ORD-2005", "customer_id": "CUST-006", "status": "completed",
     "amount": 72.00, "created_at": _yesterday_ts},

    {"order_id": "ORD-2006", "customer_id": "CUST-001", "status": "returned",
     "amount": 210.00, "created_at": _yesterday_morning_ts},

    # ── 2 days ago ────────────────────────────────────────────────
    {"order_id": "ORD-1001", "customer_id": "CUST-001", "status": "completed",
     "amount": 259.00, "created_at": _2_days_ago_ts},

    {"order_id": "ORD-1002", "customer_id": "CUST-002", "status": "completed",
     "amount": 89.00, "created_at": _2_days_ago_ts},

    {"order_id": "ORD-1003", "customer_id": "CUST-004", "status": "completed",
     "amount": 750.00, "created_at": _2_days_ago_ts},

    {"order_id": "ORD-1004", "customer_id": "CUST-005", "status": "cancelled",
     "amount": 320.00, "created_at": _2_days_ago_ts},

    {"order_id": "ORD-1005", "customer_id": "CUST-003", "status": "completed",
     "amount": 19.99, "created_at": _2_days_ago_ts},

    # ── 3 days ago ────────────────────────────────────────────────
    {"order_id": "ORD-0501", "customer_id": "CUST-001", "status": "completed",
     "amount": 175.00, "created_at": _3_days_ago_ts},

    {"order_id": "ORD-0502", "customer_id": "CUST-003", "status": "completed",
     "amount": 59.00, "created_at": _3_days_ago_ts},

    {"order_id": "ORD-0503", "customer_id": "CUST-004", "status": "completed",
     "amount": 520.00, "created_at": _3_days_ago_ts},

    {"order_id": "ORD-0504", "customer_id": "CUST-002", "status": "returned",
     "amount": 149.00, "created_at": _3_days_ago_ts},
]


# ── Transactions ──────────────────────────────────────────────────────────
# 20 transactions across 4 days, all 5 statuses covered
# Statuses: approved, declined, refunded, pending, failed
# Deliberate correlation: declined transactions ↔ failed_payment orders
MOCK_TRANSACTIONS = [
    # ── Today ─────────────────────────────────────────────────────
    {"transaction_id": "TX-5001", "customer_id": "CUST-001", "status": "declined",
     "amount": 199.99, "date": _today, "reason": "authorization_timeout",
     "payment_method": "credit_card"},

    {"transaction_id": "TX-5002", "customer_id": "CUST-004", "status": "pending",
     "amount": 450.00, "date": _today, "reason": "awaiting_confirmation",
     "payment_method": "bank_transfer"},

    {"transaction_id": "TX-5003", "customer_id": "CUST-006", "status": "approved",
     "amount": 89.50, "date": _today, "reason": "approved",
     "payment_method": "debit_card"},

    {"transaction_id": "TX-5004", "customer_id": "CUST-002", "status": "failed",
     "amount": 599.00, "date": _today, "reason": "processor_error",
     "payment_method": "credit_card"},

    {"transaction_id": "TX-5005", "customer_id": "CUST-003", "status": "approved",
     "amount": 35.00, "date": _today, "reason": "approved",
     "payment_method": "wallet"},

    # ── Yesterday ─────────────────────────────────────────────────
    {"transaction_id": "TX-4001", "customer_id": "CUST-001", "status": "declined",
     "amount": 129.99, "date": _yesterday, "reason": "authorization_timeout",
     "payment_method": "credit_card"},

    {"transaction_id": "TX-4002", "customer_id": "CUST-002", "status": "declined",
     "amount": 349.50, "date": _yesterday, "reason": "processor_503",
     "payment_method": "credit_card"},

    {"transaction_id": "TX-4003", "customer_id": "CUST-003", "status": "approved",
     "amount": 45.00, "date": _yesterday, "reason": "approved",
     "payment_method": "debit_card"},

    {"transaction_id": "TX-4004", "customer_id": "CUST-004", "status": "approved",
     "amount": 899.00, "date": _yesterday, "reason": "approved",
     "payment_method": "bank_transfer"},

    {"transaction_id": "TX-4005", "customer_id": "CUST-006", "status": "approved",
     "amount": 72.00, "date": _yesterday, "reason": "approved",
     "payment_method": "wallet"},

    {"transaction_id": "TX-4006", "customer_id": "CUST-001", "status": "refunded",
     "amount": 210.00, "date": _yesterday, "reason": "customer_requested_return",
     "payment_method": "credit_card"},

    # ── 2 days ago ────────────────────────────────────────────────
    {"transaction_id": "TX-3001", "customer_id": "CUST-001", "status": "approved",
     "amount": 259.00, "date": _2_days_ago, "reason": "approved",
     "payment_method": "credit_card"},

    {"transaction_id": "TX-3002", "customer_id": "CUST-002", "status": "approved",
     "amount": 89.00, "date": _2_days_ago, "reason": "approved",
     "payment_method": "debit_card"},

    {"transaction_id": "TX-3003", "customer_id": "CUST-001", "status": "declined",
     "amount": 50.00, "date": _2_days_ago, "reason": "insufficient_funds",
     "payment_method": "debit_card"},

    {"transaction_id": "TX-3004", "customer_id": "CUST-004", "status": "approved",
     "amount": 750.00, "date": _2_days_ago, "reason": "approved",
     "payment_method": "bank_transfer"},

    {"transaction_id": "TX-3005", "customer_id": "CUST-005", "status": "failed",
     "amount": 320.00, "date": _2_days_ago, "reason": "card_expired",
     "payment_method": "credit_card"},

    {"transaction_id": "TX-3006", "customer_id": "CUST-003", "status": "approved",
     "amount": 19.99, "date": _2_days_ago, "reason": "approved",
     "payment_method": "wallet"},

    # ── 3 days ago ────────────────────────────────────────────────
    {"transaction_id": "TX-2001", "customer_id": "CUST-001", "status": "approved",
     "amount": 175.00, "date": _3_days_ago, "reason": "approved",
     "payment_method": "credit_card"},

    {"transaction_id": "TX-2002", "customer_id": "CUST-003", "status": "approved",
     "amount": 59.00, "date": _3_days_ago, "reason": "approved",
     "payment_method": "debit_card"},

    {"transaction_id": "TX-2003", "customer_id": "CUST-002", "status": "refunded",
     "amount": 149.00, "date": _3_days_ago, "reason": "defective_product",
     "payment_method": "credit_card"},
]