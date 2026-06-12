"""
🟢 Business Data MCP Server — FastMCP with Streamable HTTP Transport.

Exposes structured business data tools via MCP protocol:

  Existing Tools:
  - get_orders(customer_id) → list
  - search_orders(min_amount, customer_id) → dict
  - get_transactions(date_range, status) → list
  - get_customer_profile(customer_id) → dict

  New Tools:
  - list_customers(segment, status) → list
  - search_customers(name, email) → list
  - get_order_summary(date_range, customer_id, min_orders) → dict
  - get_transaction_summary(date_range, customer_id, status,
                            min_amount, payment_method) → dict

Properties: Input Validated · PII Masked · Filtered · Aggregated

Architecture Mapping:
  MCP TOOLS LAYER → 🟢 Business Data Server
  Mounted into gateway.py for unified access.

References:
  - FastMCP Composition: https://fastmcp.wiki/en/servers/composition
  - FastMCP: https://gofastmcp.com
"""

from fastmcp import FastMCP

from app.data.mock_business import (
    MOCK_CUSTOMER_PROFILES,
    MOCK_ORDERS,
    MOCK_TRANSACTIONS,
)
from app.utils.masking import mask_profile
from app.utils.validators import (
    validate_customer_id,
    validate_date_range,
    validate_transaction_status,
)


# ── FastMCP Server Instance (mounted by gateway.py) ──────────────

def create_mcp_server():
    """
    Create and return the FastMCP server instance for the Business Data MCP server.

    This factory function encapsulates MCP server creation so that server
    initialization is defined in one place and can be extended later if
    additional startup configuration is needed.

    Returns:
        FastMCP: The initialized MCP server instance for business data tools.

    Raises:
        RuntimeError: If the FastMCP library is unavailable in the current
            environment.
    """
    if FastMCP is None:
        raise RuntimeError("FastMCP not installed")
    return FastMCP("business-data-server")


mcp = create_mcp_server()


# ═══════════════════════════════════════════════════════════════════════════
# EXISTING TOOLS (unchanged)
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_orders(customer_id: str) -> list[dict]:
    """Retrieve orders for a customer by customer ID.

    Args:
        customer_id: Customer identifier (must match CUST-### pattern).

    Returns:
        List of order dicts for the customer, limited to 50 results.
    """
    customer = validate_customer_id(customer_id)
    return [
        dict(order) for order in MOCK_ORDERS if order["customer_id"] == customer
    ][:50]


@mcp.tool()
def search_orders(min_amount: float = 0.0, customer_id: str = "") -> dict:
    """
    Retrieve orders filtered by minimum amount, optionally for one customer.

    Args:
        min_amount: Minimum order amount to include (must be >= 0).
        customer_id: Optional customer identifier (CUST-###). If provided,
            results are limited to that customer only.

    Returns:
        Dict with:
          - found: whether any matching orders exist
          - count: number of matching orders
          - results: matching order list
          - min_available_amount: smallest available order amount in scope
          - max_available_amount: largest available order amount in scope
          - closest_below: nearest available amount below min_amount (if any)
          - closest_above: nearest available amount above min_amount (if any)
          - message: helper message for the agent
    """
    if min_amount < 0:
        raise ValueError("min_amount must be greater than or equal to 0.")

    validated_customer = validate_customer_id(customer_id) if customer_id else ""

    scoped_orders: list[dict] = []
    for order in MOCK_ORDERS:
        if validated_customer and order.get("customer_id") != validated_customer:
            continue
        scoped_orders.append(dict(order))

    amounts: list[float] = []
    for order in scoped_orders:
        try:
            amounts.append(float(order.get("amount", 0)))
        except (TypeError, ValueError):
            continue

    if not scoped_orders or not amounts:
        return {
            "found": False,
            "count": 0,
            "results": [],
            "min_available_amount": None,
            "max_available_amount": None,
            "closest_below": None,
            "closest_above": None,
            "message": (
                f"No orders found for customer {validated_customer}."
                if validated_customer
                else "No orders available in the dataset."
            ),
        }

    matching_results: list[dict] = []
    for order in scoped_orders:
        try:
            amount = float(order.get("amount", 0))
        except (TypeError, ValueError):
            continue

        if amount >= min_amount:
            matching_results.append(order)

    sorted_amounts = sorted(amounts)
    closest_below = None
    closest_above = None

    for amt in sorted_amounts:
        if amt < min_amount:
            closest_below = amt
        if amt > min_amount and closest_above is None:
            closest_above = amt

    if matching_results:
        return {
            "found": True,
            "count": len(matching_results),
            "results": matching_results[:100],
            "min_available_amount": min(sorted_amounts),
            "max_available_amount": max(sorted_amounts),
            "closest_below": closest_below,
            "closest_above": closest_above,
            "message": f"Found {len(matching_results)} order(s) with amount >= {min_amount}.",
        }

    return {
        "found": False,
        "count": 0,
        "results": [],
        "min_available_amount": min(sorted_amounts),
        "max_available_amount": max(sorted_amounts),
        "closest_below": closest_below,
        "closest_above": closest_above,
        "message": (
            f"No orders found with amount >= {min_amount}. "
            f"Available order amounts are between {min(sorted_amounts)} and {max(sorted_amounts)}."
        ),
    }


@mcp.tool()
def get_transactions(date_range: str, status: str) -> list[dict]:
    """Retrieve transactions filtered by date range and status.

    Args:
        date_range: Date range in YYYY-MM-DD:YYYY-MM-DD format.
        status: Transaction status filter (approved, declined, refunded, pending, failed).

    Returns:
        List of transaction dicts matching filters, limited to 100 results.
    """
    start_str, end_str = validate_date_range(date_range)
    txn_status = validate_transaction_status(status)
    results = []
    for txn in MOCK_TRANSACTIONS:
        txn_date = txn.get("date", "")
        if start_str <= txn_date <= end_str:
            if txn_status == "all" or txn.get("status") == txn_status:
                results.append(dict(txn))
    return results[:100]


@mcp.tool()
def get_customer_profile(customer_id: str) -> dict:
    """Retrieve customer profile with PII masking applied.

    Args:
        customer_id: Customer identifier (must match CUST-### pattern).

    Returns:
        Dict with customer profile. Email and phone fields are masked.
        Returns {found: False} if customer not found.
    """
    customer = validate_customer_id(customer_id)
    profile = MOCK_CUSTOMER_PROFILES.get(customer)
    if profile is None:
        return {"found": False, "customer_id": customer}
    masked = mask_profile(profile)
    masked["found"] = True
    return masked


# ═══════════════════════════════════════════════════════════════════════════
# NEW TOOLS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_customers(segment: str = "", status: str = "") -> dict:
    """List all customers with optional segment and status filters.

    Supports queries like:
      - "Show all customers"
      - "How many customers do we have?"
      - "Show enterprise customers"
      - "Show inactive customers"
      - "List active SMB customers"

    Args:
        segment: Optional segment filter (enterprise, mid_market, smb).
                 Empty string = all segments.
        status: Optional status filter (active, inactive).
                Empty string = all statuses.

    Returns:
        Dict with:
          - total_count: number of matching customers
          - customers: list of customer summaries (PII masked)
          - count_by_segment: breakdown by segment
          - count_by_status: breakdown by status
    """
    results = []

    for profile in MOCK_CUSTOMER_PROFILES.values():
        # Apply segment filter
        if segment and profile.get("segment", "") != segment.strip().lower():
            continue

        # Apply status filter
        if status and profile.get("status", "") != status.strip().lower():
            continue

        # Mask PII before returning
        masked = mask_profile(profile)
        results.append(masked)

    # Count by segment
    count_by_segment: dict[str, int] = {}
    for c in results:
        seg = c.get("segment", "unknown")
        count_by_segment[seg] = count_by_segment.get(seg, 0) + 1

    # Count by status
    count_by_status: dict[str, int] = {}
    for c in results:
        st = c.get("status", "unknown")
        count_by_status[st] = count_by_status.get(st, 0) + 1

    return {
        "total_count": len(results),
        "customers": results,
        "count_by_segment": count_by_segment,
        "count_by_status": count_by_status,
    }


@mcp.tool()
def search_customers(name: str = "", email: str = "") -> dict:
    """Search customers by name or email (partial, case-insensitive match).

    Supports queries like:
      - "Find customer Avery"
      - "Search customer by name Morgan"
      - "Look up customer with email stone"

    Args:
        name: Optional partial name match (case-insensitive).
        email: Optional partial email match (case-insensitive).

    Returns:
        Dict with:
          - found: whether any customers matched
          - count: number of matching customers
          - results: list of matching customer profiles (PII masked)
          - message: helper message
    """
    if not name and not email:
        return {
            "found": False,
            "count": 0,
            "results": [],
            "message": "Please provide a name or email to search.",
        }

    name_lower = name.strip().lower() if name else ""
    email_lower = email.strip().lower() if email else ""

    results = []

    for profile in MOCK_CUSTOMER_PROFILES.values():
        matched = False

        if name_lower and name_lower in profile.get("name", "").lower():
            matched = True

        if email_lower and email_lower in profile.get("email", "").lower():
            matched = True

        if matched:
            masked = mask_profile(profile)
            results.append(masked)

    if results:
        return {
            "found": True,
            "count": len(results),
            "results": results,
            "message": f"Found {len(results)} customer(s) matching the search.",
        }

    return {
        "found": False,
        "count": 0,
        "results": [],
        "message": "No customers found matching the search criteria.",
    }


@mcp.tool()
def get_order_summary(
    date_range: str = "",
    customer_id: str = "",
    min_orders: int = 0,
) -> dict:
    """Get aggregated order statistics with optional filters.

    Supports queries like:
      - "Show customers who ordered repeatedly this week"
      - "What is today's total order revenue?"
      - "Average order value for CUST-001"
      - "How many orders were placed yesterday?"
      - "Which customer placed the most orders?"
      - "Show order breakdown by status"

    Args:
        date_range: Optional YYYY-MM-DD:YYYY-MM-DD filter.
        customer_id: Optional CUST-### filter for single customer.
        min_orders: Optional minimum order count per customer
                    (use to find repeat customers, e.g., min_orders=2).

    Returns:
        Dict with:
          - total_orders: number of matching orders
          - total_revenue: sum of all order amounts
          - avg_order_value: average order amount
          - orders_by_status: count breakdown by status
          - orders_by_customer: per-customer counts and totals (sorted)
          - repeat_customers: customers with >= min_orders (or >= 2)
          - message: helper message if no results
    """
    # ── Filter by date range ──────────────────────────────────
    filtered = list(MOCK_ORDERS)

    if date_range:
        start, end = validate_date_range(date_range)
        filtered = [
            o for o in filtered
            if start <= o["created_at"][:10] <= end
        ]

    # ── Filter by customer ────────────────────────────────────
    if customer_id:
        cid = validate_customer_id(customer_id)
        filtered = [o for o in filtered if o["customer_id"] == cid]

    # ── Empty result ──────────────────────────────────────────
    if not filtered:
        return {
            "total_orders": 0,
            "total_revenue": 0.0,
            "avg_order_value": 0.0,
            "orders_by_status": {},
            "orders_by_customer": [],
            "repeat_customers": [],
            "message": "No orders found for the given filters.",
        }

    # ── Basic aggregation ─────────────────────────────────────
    total_revenue = round(sum(o["amount"] for o in filtered), 2)
    avg_value = round(total_revenue / len(filtered), 2)

    # ── Count by status ───────────────────────────────────────
    status_counts: dict[str, int] = {}
    for o in filtered:
        s = o["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    # ── Per-customer aggregation ──────────────────────────────
    customer_data: dict[str, dict] = {}
    for o in filtered:
        cid = o["customer_id"]
        if cid not in customer_data:
            customer_data[cid] = {
                "customer_id": cid,
                "order_count": 0,
                "total_amount": 0.0,
            }
        customer_data[cid]["order_count"] += 1
        customer_data[cid]["total_amount"] += o["amount"]

    # Round totals
    for cd in customer_data.values():
        cd["total_amount"] = round(cd["total_amount"], 2)

    # Sort by order count descending
    orders_by_customer = sorted(
        customer_data.values(),
        key=lambda x: x["order_count"],
        reverse=True,
    )

    # ── Repeat customers ──────────────────────────────────────
    threshold = min_orders if min_orders > 0 else 2
    repeat_customers = [
        c for c in orders_by_customer if c["order_count"] >= threshold
    ]

    return {
        "total_orders": len(filtered),
        "total_revenue": total_revenue,
        "avg_order_value": avg_value,
        "orders_by_status": status_counts,
        "orders_by_customer": orders_by_customer,
        "repeat_customers": repeat_customers,
    }


@mcp.tool()
def get_transaction_summary(
    date_range: str = "",
    customer_id: str = "",
    status: str = "",
    min_amount: float = 0.0,
    payment_method: str = "",
) -> dict:
    """Get aggregated transaction statistics with flexible filters.

    Supports queries like:
      - "What is the decline rate?"
      - "Compare approved vs declined transactions"
      - "Total revenue today"
      - "Show customers with most declined transactions"
      - "What is the refund rate this week?"
      - "Which payment method has most failures?"
      - "Show high-value declined transactions"
      - "Transaction summary for CUST-001"

    Args:
        date_range: Optional YYYY-MM-DD:YYYY-MM-DD filter.
        customer_id: Optional CUST-### filter for single customer.
        status: Optional status filter
                (approved, declined, refunded, pending, failed).
        min_amount: Optional minimum transaction amount filter.
        payment_method: Optional payment method filter
                        (credit_card, debit_card, bank_transfer, wallet).

    Returns:
        Dict with:
          - total_count, total_amount, avg_transaction_amount
          - count_by_status, amount_by_status
          - approval_rate, decline_rate, refund_rate, failure_rate
          - count_by_payment_method
          - transactions_by_customer (with per-status counts)
          - customers_with_declines
          - highest_transaction, lowest_transaction
          - message: helper message if no results
    """
    # ── Filter by date range ──────────────────────────────────
    filtered = list(MOCK_TRANSACTIONS)

    if date_range:
        start, end = validate_date_range(date_range)
        filtered = [t for t in filtered if start <= t["date"] <= end]

    # ── Filter by customer ────────────────────────────────────
    if customer_id:
        cid = validate_customer_id(customer_id)
        filtered = [t for t in filtered if t["customer_id"] == cid]

    # ── Filter by status ──────────────────────────────────────
    if status:
        normalized_status = validate_transaction_status(status)
        filtered = [t for t in filtered if t["status"] == normalized_status]

    # ── Filter by minimum amount ──────────────────────────────
    if min_amount > 0:
        filtered = [t for t in filtered if t["amount"] >= min_amount]

    # ── Filter by payment method ──────────────────────────────
    if payment_method:
        pm = payment_method.strip().lower()
        filtered = [t for t in filtered if t.get("payment_method", "") == pm]

    # ── Empty result ──────────────────────────────────────────
    if not filtered:
        return {
            "total_count": 0,
            "total_amount": 0.0,
            "avg_transaction_amount": 0.0,
            "count_by_status": {},
            "amount_by_status": {},
            "approval_rate": 0.0,
            "decline_rate": 0.0,
            "refund_rate": 0.0,
            "failure_rate": 0.0,
            "count_by_payment_method": {},
            "transactions_by_customer": [],
            "customers_with_declines": [],
            "highest_transaction": None,
            "lowest_transaction": None,
            "message": "No transactions found for the given filters.",
        }

    # ── Basic aggregation ─────────────────────────────────────
    total_count = len(filtered)
    total_amount = round(sum(t["amount"] for t in filtered), 2)
    avg_amount = round(total_amount / total_count, 2)

    # ── Count and amount by status ────────────────────────────
    count_by_status: dict[str, int] = {}
    amount_by_status: dict[str, float] = {}

    for t in filtered:
        s = t["status"]
        count_by_status[s] = count_by_status.get(s, 0) + 1
        amount_by_status[s] = round(
            amount_by_status.get(s, 0.0) + t["amount"], 2
        )

    # ── Rate calculations ─────────────────────────────────────
    approval_rate = round(
        (count_by_status.get("approved", 0) / total_count) * 100, 1
    )
    decline_rate = round(
        (count_by_status.get("declined", 0) / total_count) * 100, 1
    )
    refund_rate = round(
        (count_by_status.get("refunded", 0) / total_count) * 100, 1
    )
    failure_rate = round(
        (count_by_status.get("failed", 0) / total_count) * 100, 1
    )

    # ── Count by payment method ───────────────────────────────
    count_by_pm: dict[str, int] = {}
    for t in filtered:
        pm = t.get("payment_method", "unknown")
        count_by_pm[pm] = count_by_pm.get(pm, 0) + 1

    # ── Per-customer aggregation ──────────────────────────────
    customer_data: dict[str, dict] = {}

    for t in filtered:
        cid = t["customer_id"]
        if cid not in customer_data:
            customer_data[cid] = {
                "customer_id": cid,
                "transaction_count": 0,
                "total_amount": 0.0,
                "approved_count": 0,
                "declined_count": 0,
                "refunded_count": 0,
                "failed_count": 0,
                "pending_count": 0,
            }
        cd = customer_data[cid]
        cd["transaction_count"] += 1
        cd["total_amount"] += t["amount"]

        status_key = f"{t['status']}_count"
        if status_key in cd:
            cd[status_key] += 1

    # Round totals
    for cd in customer_data.values():
        cd["total_amount"] = round(cd["total_amount"], 2)

    # Sort by transaction count descending
    transactions_by_customer = sorted(
        customer_data.values(),
        key=lambda x: x["transaction_count"],
        reverse=True,
    )

    # Customers with at least 1 decline
    customers_with_declines = [
        c for c in transactions_by_customer if c["declined_count"] > 0
    ]

    # ── Highest and lowest ────────────────────────────────────
    highest = max(filtered, key=lambda t: t["amount"])
    lowest = min(filtered, key=lambda t: t["amount"])

    highest_transaction = {
        "transaction_id": highest["transaction_id"],
        "customer_id": highest["customer_id"],
        "amount": highest["amount"],
        "status": highest["status"],
        "date": highest["date"],
    }

    lowest_transaction = {
        "transaction_id": lowest["transaction_id"],
        "customer_id": lowest["customer_id"],
        "amount": lowest["amount"],
        "status": lowest["status"],
        "date": lowest["date"],
    }

    return {
        "total_count": total_count,
        "total_amount": total_amount,
        "avg_transaction_amount": avg_amount,
        "count_by_status": count_by_status,
        "amount_by_status": amount_by_status,
        "approval_rate": approval_rate,
        "decline_rate": decline_rate,
        "refund_rate": refund_rate,
        "failure_rate": failure_rate,
        "count_by_payment_method": count_by_pm,
        "transactions_by_customer": transactions_by_customer,
        "customers_with_declines": customers_with_declines,
        "highest_transaction": highest_transaction,
        "lowest_transaction": lowest_transaction,
    }


# ── Standalone Entry Point (optional — for running individually) ──
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8011, path="/mcp")