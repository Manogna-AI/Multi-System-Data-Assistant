from app.agents.orchestrator import Orchestrator


class RootAgent:
    """Root ADK-style Data Analyst Assistant.

    This root agent delegates exclusively to domain agents. Domain agents use MCP
    toolset wrappers and do not import or query enterprise data sources directly.
    """

    name = "data_analyst_assistant"
    instruction = "Answer business and operations questions using only MCP-exposed tools."

    def __init__(self) -> None:
        self.orchestrator = Orchestrator()

    def run(self, query: str, confirm_action: bool = False):
        return self.orchestrator.run(query=query, confirm_action=confirm_action)
