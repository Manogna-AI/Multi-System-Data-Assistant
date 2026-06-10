"""
Intent Classifier — Optional deterministic utility for structured intent extraction.

⚠️ THIS IS NOT A GOOGLE ADK AGENT.
This is a pure Python utility class retained for:
- Structured intent tagging in API responses (analytics/logging).
- Pre-routing validation before ADK agent execution.
- Fallback classification when LLM routing is unavailable.

The ACTUAL intent classification and routing is handled by the root_agent.py
(ADK LlmAgent) using ADK's native sub-agent transfer mechanism.

Previously located at: app/agents/intent_classifier.py
Moved to: app/utils/intent_classifier.py (correct architectural placement)
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field


class IntentCategory(StrEnum):
    """Supported intent categories matching the architecture diagram."""

    OBSERVE = "observe"
    BUSINESS = "business"
    ACTION = "action"
    CROSS_QUERY = "cross_query"
    UNKNOWN = "unknown"


class IntentResult(BaseModel):
    """Structured result from intent classification."""

    category: IntentCategory = Field(description="Primary intent category")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence")
    keywords_matched: list[str] = Field(default_factory=list)
    is_cross_domain: bool = Field(default=False)


# ── Keyword Patterns ──────────────────────────────────────────────────────
_OBSERVE_KEYWORDS = {
    "log", "logs", "metric", "metrics", "alert", "alerts",
    "error", "errors", "latency", "cpu", "memory", "health",
    "monitoring", "throughput", "uptime", "downtime", "performance",
    "error_rate", "service health", "infrastructure",
}

_BUSINESS_KEYWORDS = {
    "order", "orders", "customer", "transaction", "transactions",
    "revenue", "sales", "payment", "decline", "declined",
    "complaint", "complaints", "profile", "business",
    "invoice", "refund", "billing",
}

_ACTION_KEYWORDS = {
    "restart", "scale", "ticket", "create ticket", "replicas",
    "reboot", "deploy", "rollback", "incident",
    "scale up", "scale down",
}


class IntentClassifier:
    """Deterministic intent classifier for structured query routing.

    This is an OPTIONAL utility — the root ADK agent handles actual routing
    via LLM reasoning. Use this for API-level intent tagging and analytics.

    Usage:
        classifier = IntentClassifier()
        result = classifier.classify("Why did revenue drop yesterday?")
        # result.category == IntentCategory.CROSS_QUERY
        # result.is_cross_domain == True
    """

    def classify(self, query: str) -> IntentResult:
        """Classify a user query into an intent category.

        Args:
            query: The user's natural language query.

        Returns:
            IntentResult with category, confidence, and matched keywords.
        """
        query_lower = query.lower()
        tokens = set(re.findall(r"\w+", query_lower))

        observe_matches = tokens & _OBSERVE_KEYWORDS
        business_matches = tokens & _BUSINESS_KEYWORDS
        action_matches = tokens & _ACTION_KEYWORDS

        categories_matched = []
        if observe_matches:
            categories_matched.append(
                (IntentCategory.OBSERVE, len(observe_matches), list(observe_matches))
            )
        if business_matches:
            categories_matched.append(
                (IntentCategory.BUSINESS, len(business_matches), list(business_matches))
            )
        if action_matches:
            categories_matched.append(
                (IntentCategory.ACTION, len(action_matches), list(action_matches))
            )

        if not categories_matched:
            return IntentResult(
                category=IntentCategory.UNKNOWN,
                confidence=0.0,
                keywords_matched=[],
                is_cross_domain=False,
            )

        is_cross = len(categories_matched) > 1

        if is_cross:
            all_keywords = []
            for _, _, kws in categories_matched:
                all_keywords.extend(kws)
            return IntentResult(
                category=IntentCategory.CROSS_QUERY,
                confidence=0.8,
                keywords_matched=all_keywords,
                is_cross_domain=True,
            )

        best = max(categories_matched, key=lambda x: x[1])
        total_keywords = sum(
            len(_OBSERVE_KEYWORDS), len(_BUSINESS_KEYWORDS), len(_ACTION_KEYWORDS)
        ) if False else max(best[1], 1)

        return IntentResult(
            category=best[0],
            confidence=min(best[1] / 3.0, 1.0),
            keywords_matched=best[2],
            is_cross_domain=False,
        )