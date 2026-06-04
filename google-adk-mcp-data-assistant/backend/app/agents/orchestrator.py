from app.agents.action_agent import ActionAgent
from app.agents.business_agent import BusinessDataAgent
from app.agents.intent_classifier import IntentCategory, IntentClassifier, IntentResult
from app.agents.observability_agent import ObservabilityAgent
from app.mcp_clients.action_toolset import ToolTrace as ActionTrace


class Orchestrator:
    def __init__(self) -> None:
        self.intent_classifier = IntentClassifier()
        self.observability_agent = ObservabilityAgent()
        self.business_agent = BusinessDataAgent()
        self.action_agent = ActionAgent()

    def run(self, query: str, confirm_action: bool = False) -> tuple[IntentResult, dict, list]:
        intent = self.intent_classifier.classify(query)
        service = intent.service_name or "payment-service"
        customer = intent.customer_id or "CUST-001"
        traces: list = []
        payload: dict = {}

        if intent.category == IntentCategory.OBSERVE:
            payload["observability"], obs_traces = self.observability_agent.answer(service)
            traces.extend(obs_traces)
        elif intent.category == IntentCategory.BUSINESS:
            payload["business"], biz_traces = self.business_agent.answer(customer)
            traces.extend(biz_traces)
        elif intent.category == IntentCategory.ACTION:
            payload["action"], action_traces = self.action_agent.answer(query, service, confirm_action)
            traces.extend(action_traces)
        else:
            payload["business"], biz_traces = self.business_agent.answer(customer)
            payload["observability"], obs_traces = self.observability_agent.answer(service)
            traces.extend(biz_traces + obs_traces)
        return intent, payload, traces
