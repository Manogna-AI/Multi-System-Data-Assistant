"""
Tests for the 🟢 Business Data MCP Server tool functions.

Properties tested: Input Validated · PII Masked · Filtered
"""

import pytest

from app.utils.errors import DomainValidationError
from mcp_servers.business_data_server import (
    get_customer_profile,
    get_orders,
    get_transactions,
)


# ── get_orders Tests ──────────────────────────────────────────────────────

def test_get_orders_valid_customer():
    """Valid customer ID returns matching orders."""
    orders = get_orders("CUST-001")
    assert orders
    assert all(order["customer_id"] == "CUST-001" for order in orders)


def test_get_orders_requires_customer_id():
    """Empty customer ID is rejected."""
    with pytest.raises(DomainValidationError):
        get_orders("")


def test_get_orders_rejects_invalid_format():
    """Customer ID not matching CUST-### pattern is rejected."""
    with pytest.raises(DomainValidationError):
        get_orders("INVALID-001")


def test_get_orders_returns_empty_for_unknown_customer():
    """Valid format but non-existent customer returns empty list."""
    orders = get_orders("CUST-999")
    assert orders == []


# ── get_transactions Tests ────────────────────────────────────────────────

def test_get_transactions_valid_request():
    """Valid date range and status returns matching transactions."""
    txns = get_transactions("2026-06-03:2026-06-03", "declined")
    assert txns
    assert all(tx["status"] == "declined" for tx in txns)


def test_get_transactions_validates_status():
    """Invalid transaction status is rejected."""
    with pytest.raises(DomainValidationError):
        get_transactions("2026-06-03:2026-06-03", "all")


def test_get_transactions_validates_date_format():
    """Invalid date range format is rejected."""
    with pytest.raises(DomainValidationError):
        get_transactions("2026/06/03-2026/06/03", "approved")


def test_get_transactions_rejects_end_before_start():
    """End date before start date is rejected."""
    with pytest.raises(DomainValidationError):
        get_transactions("2026-06-05:2026-06-03", "approved")


# ── get_customer_profile Tests ────────────────────────────────────────────

def test_customer_profile_masks_pii():
    """PII fields (email, phone) are masked in the response."""
    profile = get_customer_profile("CUST-001")

    # Email: "avery.stone@example.com" → "a***@example.com"
    assert profile["found"] is True
    assert profile["email"].startswith("a***@")
    assert "avery.stone" not in profile["email"]

    # Phone: "+1-555-0101" → "***-***-0101"
    assert profile["phone"].startswith("***-***-")
    assert profile["phone"] == "***-***-0101"


def test_customer_profile_not_found():
    """Non-existent customer returns found=False."""
    profile = get_customer_profile("CUST-999")
    assert profile["found"] is False
    assert profile["customer_id"] == "CUST-999"


def test_customer_profile_preserves_non_pii_fields():
    """Non-PII fields are returned unmasked."""
    profile = get_customer_profile("CUST-001")
    assert profile["name"] == "Avery Stone"
    assert profile["segment"] == "enterprise"
    assert profile["open_complaints"] == 2