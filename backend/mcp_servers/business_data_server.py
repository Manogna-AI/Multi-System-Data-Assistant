"""
🟢 Business Data MCP Server — FastMCP with Streamable HTTP Transport.

Exposes structured business data tools via MCP protocol:
  - get_orders(customer_id) → list
  - search_orders(min_amount, customer_id) → list
  - get_transactions(date_range, status) → list
  - get_customer_profile(customer_id) → dict

Properties: Input Validated · PII Masked · Filtered

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
    if FastMCP is None:
        raise RuntimeError("FastMCP not installed")
    return FastMCP("business-data-server")

mcp = create_mcp_server()


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


# ── Standalone Entry Point (optional — for running individually) ──
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8011, path="/mcp")