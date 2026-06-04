from app.agents.intent_classifier import IntentCategory, IntentClassifier


def test_revenue_drop_routes_to_cross_query():
    intent = IntentClassifier().classify("Why did revenue drop yesterday?")
    assert intent.category == IntentCategory.CROSS_QUERY
    assert intent.service_name == "payment-service"


def test_restart_routes_to_action():
    intent = IntentClassifier().classify("Restart payment service")
    assert intent.category == IntentCategory.ACTION
    assert intent.requires_confirmation is True
