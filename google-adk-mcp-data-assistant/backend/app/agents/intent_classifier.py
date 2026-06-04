from enum import StrEnum
from pydantic import BaseModel


class IntentCategory(StrEnum):
    OBSERVE = "OBSERVE"
    BUSINESS = "BUSINESS"
    ACTION = "ACTION"
    CROSS_QUERY = "CROSS_QUERY"


class IntentResult(BaseModel):
    category: IntentCategory
    requires_confirmation: bool = False
    service_name: str | None = None
    customer_id: str | None = None
    rationale: str


class IntentClassifier:
    """Deterministic intent classifier suitable for tests and safe routing."""

    def classify(self, query: str) -> IntentResult:
        q = query.lower()
        service = self._extract_service(q)
        customer = self._extract_customer(q)
        action_terms = {"restart", "scale", "create ticket", "open ticket"}
        observe_terms = {"log", "logs", "metric", "alert", "error", "latency", "system"}
        business_terms = {"revenue", "order", "transaction", "customer", "complaint", "payment", "impact"}

        if any(term in q for term in action_terms):
            return IntentResult(category=IntentCategory.ACTION, requires_confirmation=True, service_name=service, customer_id=customer, rationale="Action verb detected; explicit confirmation required.")
        has_observe = any(term in q for term in observe_terms)
        has_business = any(term in q for term in business_terms)
        if has_observe and has_business:
            return IntentResult(category=IntentCategory.CROSS_QUERY, service_name=service, customer_id=customer, rationale="Query spans business and observability domains.")
        if has_observe:
            return IntentResult(category=IntentCategory.OBSERVE, service_name=service, customer_id=customer, rationale="Observability terms detected.")
        if has_business:
            return IntentResult(category=IntentCategory.BUSINESS, service_name=service, customer_id=customer, rationale="Business terms detected.")
        return IntentResult(category=IntentCategory.CROSS_QUERY, service_name=service, customer_id=customer, rationale="Defaulting to cross-query for broad analyst question.")

    @staticmethod
    def _extract_service(q: str) -> str | None:
        aliases = {"payment": "payment-service", "checkout": "checkout-service", "orders": "orders-service", "inventory": "inventory-service"}
        for key, value in aliases.items():
            if key in q:
                return value
        return "payment-service" if "revenue" in q or "transaction" in q else None

    @staticmethod
    def _extract_customer(q: str) -> str | None:
        for token in q.replace("?", "").replace(",", " ").split():
            if token.upper().startswith("CUST-"):
                return token.upper()
        return "CUST-001" if "customer" in q or "complaint" in q else None
