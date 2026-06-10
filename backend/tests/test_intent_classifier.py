"""
Tests for the deterministic IntentClassifier utility.

NOTE: This classifier is an OPTIONAL utility (app/utils/intent_classifier.py).
Actual intent classification in production is handled by the ADK Root Agent
via LLM reasoning and sub-agent descriptions. These tests validate the
keyword-based fallback classifier only.
"""

from app.utils.intent_classifier import (
    IntentCategory,
    IntentClassifier,
    IntentResult,
)

classifier = IntentClassifier()


# ── OBSERVE Intent ────────────────────────────────────────────────────────


def test_logs_query_routes_to_observe():
    """Pure observability query with clear keywords."""
    result = classifier.classify("Show me error logs for the service")
    assert result.category == IntentCategory.OBSERVE
    assert "logs" in result.keywords_matched or "error" in result.keywords_matched
    assert result.is_cross_domain is False



def test_metrics_query_routes_to_observe():
    """Metrics-focused query."""
    result = classifier.classify("What is the latency and throughput?")
    assert result.category == IntentCategory.OBSERVE
    assert result.confidence > 0


def test_alerts_query_routes_to_observe():
    """Alerts-focused query."""
    result = classifier.classify("Are there any active alerts?")
    assert result.category == IntentCategory.OBSERVE


# ── BUSINESS Intent ───────────────────────────────────────────────────────

def test_orders_query_routes_to_business():
    """Pure business query about orders."""
    result = classifier.classify("Show me orders for customer CUST-001")
    assert result.category == IntentCategory.BUSINESS
    assert "orders" in result.keywords_matched or "customer" in result.keywords_matched
    assert result.is_cross_domain is False


def test_revenue_query_routes_to_business():
    """Revenue query — only BUSINESS keywords match (no OBSERVE keywords)."""
    result = classifier.classify("Why did revenue drop yesterday?")
    assert result.category == IntentCategory.BUSINESS
    assert "revenue" in result.keywords_matched


def test_transactions_query_routes_to_business():
    """Transaction-focused query."""
    result = classifier.classify("Show me declined transactions")
    assert result.category == IntentCategory.BUSINESS


# ── ACTION Intent ─────────────────────────────────────────────────────────

def test_restart_only_routes_to_action():
    """Pure action query with only ACTION keywords."""
    result = classifier.classify("Restart the service now")
    assert result.category == IntentCategory.ACTION
    assert "restart" in result.keywords_matched


def test_scale_query_routes_to_action():
    """Scaling query."""
    result = classifier.classify("Scale up to 3 replicas")
    assert result.category == IntentCategory.ACTION


def test_ticket_query_routes_to_action():
    """Ticket creation query."""
    result = classifier.classify("Create a ticket for the incident")
    assert result.category == IntentCategory.ACTION


# ── CROSS-QUERY Intent ───────────────────────────────────────────────────

def test_cross_domain_observe_and_business():
    """Query spanning OBSERVE + BUSINESS domains."""
    result = classifier.classify(
        "Compare system errors vs customer complaints"
    )
    assert result.category == IntentCategory.CROSS_QUERY
    assert result.is_cross_domain is True
    assert result.confidence > 0


def test_cross_domain_restart_and_payment():
    """Query spanning ACTION + BUSINESS domains.
    'restart' → ACTION, 'payment' → BUSINESS → CROSS_QUERY.
    """
    result = classifier.classify("Restart payment service")
    assert result.category == IntentCategory.CROSS_QUERY
    assert result.is_cross_domain is True


def test_cross_domain_errors_and_revenue():
    """Query spanning OBSERVE + BUSINESS domains."""
    result = classifier.classify(
        "Show me error metrics and declined transactions"
    )
    assert result.category == IntentCategory.CROSS_QUERY
    assert result.is_cross_domain is True


# ── UNKNOWN Intent ────────────────────────────────────────────────────────

def test_unknown_query():
    """Query with no matching keywords."""
    result = classifier.classify("Hello, how are you?")
    assert result.category == IntentCategory.UNKNOWN
    assert result.confidence == 0.0
    assert result.keywords_matched == []


# ── IntentResult Structure ────────────────────────────────────────────────

def test_intent_result_structure():
    """Verify IntentResult has all expected fields."""
    result = classifier.classify("Show me logs")
    assert isinstance(result, IntentResult)
    assert hasattr(result, "category")
    assert hasattr(result, "confidence")
    assert hasattr(result, "keywords_matched")
    assert hasattr(result, "is_cross_domain")
    assert isinstance(result.keywords_matched, list)
    assert isinstance(result.confidence, float)
    assert 0.0 <= result.confidence <= 1.0