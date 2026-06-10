"""
🟢 Business Data MCP Server — FastMCP with Streamable HTTP Transport.

Exposes structured business data tools via MCP protocol:
  - get_orders(customer_id) → list
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
mcp = FastMCP("business-data-server")


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