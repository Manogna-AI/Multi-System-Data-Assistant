import importlib
import importlib.util
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """LiteLLM abstraction with Gemini primary and Ollama fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def summarize(self, query: str, context: dict) -> str:
        prompt = f"Summarize the enterprise assistant findings for query: {query}\nContext: {context}"
        if importlib.util.find_spec("litellm") is None:
            return self._deterministic_summary(query, context)
        litellm = importlib.import_module("litellm")
        for model in (self.settings.primary_model, self.settings.fallback_model):
            try:
                response = await litellm.acompletion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=self.settings.litellm_timeout_seconds,
                    api_base=self.settings.ollama_base_url if model.startswith("ollama/") else None,
                )
                return response["choices"][0]["message"]["content"]
            except Exception as exc:
                logger.warning("llm_provider_failed", extra={"model": model, "error": str(exc)})
        return self._deterministic_summary(query, context)

    @staticmethod
    def _deterministic_summary(query: str, context: dict) -> str:
        if "action" in context:
            result = context["action"].get("action_result", {})
            return result.get("message") or f"Action status: {result.get('status', 'unknown')}"
        parts = []
        business = context.get("business", {})
        observability = context.get("observability", {})
        if business:
            declined = len(business.get("declined_transactions", []))
            parts.append(f"Business data shows {declined} declined transactions in the selected window")
        if observability:
            metric = observability.get("metrics", {})
            alerts = observability.get("alerts", [])
            value = metric.get("value")
            baseline = metric.get("baseline")
            parts.append(f"Observability data shows error_rate={value} versus baseline={baseline} with {len(alerts)} active alerts")
        if not parts:
            parts.append("No matching data was found through the configured MCP tools")
        return "; ".join(parts) + "."
