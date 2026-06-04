import pytest
from app.utils.errors import DomainValidationError
from mcp_servers.business_data_server import get_customer_profile, get_orders, get_transactions


def test_get_orders_valid_customer():
    orders = get_orders("CUST-001")
    assert orders
    assert all(order["customer_id"] == "CUST-001" for order in orders)


def test_get_orders_requires_customer_id():
    with pytest.raises(DomainValidationError):
        get_orders("")


def test_get_transactions_validates_status():
    with pytest.raises(DomainValidationError):
        get_transactions("2026-06-03:2026-06-03", "all")


def test_customer_profile_masks_pii():
    profile = get_customer_profile("CUST-001")
    assert profile["email"].startswith("a***@")
    assert profile["phone"].startswith("***-***-")
    assert "555-0101" not in profile["phone"]
