MOCK_ORDERS = [
    {"order_id": "ORD-1001", "customer_id": "CUST-001", "status": "failed_payment", "amount": 129.99, "created_at": "2026-06-03T09:07:00Z"},
    {"order_id": "ORD-1002", "customer_id": "CUST-001", "status": "completed", "amount": 59.00, "created_at": "2026-06-02T12:01:00Z"},
    {"order_id": "ORD-2001", "customer_id": "CUST-002", "status": "failed_payment", "amount": 349.50, "created_at": "2026-06-03T09:18:00Z"},
]

MOCK_TRANSACTIONS = [
    {"transaction_id": "TX-9001", "customer_id": "CUST-001", "status": "declined", "amount": 129.99, "date": "2026-06-03", "reason": "authorization_timeout"},
    {"transaction_id": "TX-9002", "customer_id": "CUST-002", "status": "declined", "amount": 349.50, "date": "2026-06-03", "reason": "processor_503"},
    {"transaction_id": "TX-9003", "customer_id": "CUST-003", "status": "approved", "amount": 79.00, "date": "2026-06-03", "reason": "approved"},
    {"transaction_id": "TX-8999", "customer_id": "CUST-001", "status": "approved", "amount": 59.00, "date": "2026-06-02", "reason": "approved"},
]

MOCK_CUSTOMER_PROFILES = {
    "CUST-001": {"customer_id": "CUST-001", "name": "Avery Stone", "email": "avery.stone@example.com", "phone": "+1-555-0101", "segment": "enterprise", "open_complaints": 2},
    "CUST-002": {"customer_id": "CUST-002", "name": "Morgan Lee", "email": "morgan.lee@example.com", "phone": "+1-555-0102", "segment": "mid_market", "open_complaints": 1},
    "CUST-003": {"customer_id": "CUST-003", "name": "Riley Kim", "email": "riley.kim@example.com", "phone": "+1-555-0103", "segment": "smb", "open_complaints": 0},
}
