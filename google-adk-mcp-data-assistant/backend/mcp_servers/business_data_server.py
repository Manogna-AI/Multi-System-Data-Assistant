import importlib
import importlib.util


def build_mcp(name: str):
    if importlib.util.find_spec("fastmcp") is None:
        class LocalFastMCP:
            def __init__(self, server_name: str):
                self.name = server_name
            def tool(self):
                def decorator(func):
                    return func
                return decorator
            def run(self, *_, **__):
                return None
        return LocalFastMCP(name)
    return importlib.import_module("fastmcp").FastMCP(name)

from app.data.mock_business import MOCK_CUSTOMER_PROFILES, MOCK_ORDERS, MOCK_TRANSACTIONS
from app.utils.masking import mask_profile
from app.utils.validators import validate_customer_id, validate_date_range, validate_transaction_status

mcp = build_mcp("business-data-server")


@mcp.tool()
def get_orders(customer_id: str) -> list[dict]:
    customer = validate_customer_id(customer_id)
    return [dict(order) for order in MOCK_ORDERS if order["customer_id"] == customer][:50]


@mcp.tool()
def get_transactions(date_range: str, status: str) -> list[dict]:
    start, end = validate_date_range(date_range)
    valid_status = validate_transaction_status(status)
    return [
        dict(tx)
        for tx in MOCK_TRANSACTIONS
        if start <= tx["date"] <= end and tx["status"] == valid_status
    ][:100]


@mcp.tool()
def get_customer_profile(customer_id: str) -> dict:
    customer = validate_customer_id(customer_id)
    profile = MOCK_CUSTOMER_PROFILES.get(customer)
    if profile is None:
        return {"customer_id": customer, "found": False}
    masked = mask_profile(profile)
    masked["found"] = True
    return masked


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8002, path="/mcp")
