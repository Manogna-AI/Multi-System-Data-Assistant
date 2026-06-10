"""
🟢 Business Data Agent — Google ADK LlmAgent with MCP Toolset.

Connects to the Business Data MCP Server (Port 8011) to query
customer profiles, orders, and transactions.

Architecture Mapping:
  💼 Business Data Agent → McpToolset → Business Data Server (Port 8011)
  Tools: get_orders, get_transactions, get_customer_profile
  Properties: Input Validated · PII Masked · Filtered

References:
  - LlmAgent: https://adk.dev/agents/llm-agents/
  - McpToolset: https://adk.dev/tools-custom/mcp-tools/
"""

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)

from app.config import get_settings

# ── Load Settings at Module Level ────────────────────────────────
settings = get_settings()

# ── Agent Instruction ────────────────────────────────────────────
BUSINESS_INSTRUCTION = """You are a **Business Data Analyst** agent.

## Capabilities

You have access to MCP tools that let you query:
- **Customer Profiles** — Retrieve customer information by customer ID
  using get_customer_profile(customer_id).
- **Orders** — Query order details, statuses, and history by customer ID
  using get_orders(customer_id).
- **Transactions** — Analyze transaction data filtered by date range
  and status (e.g., "declined", "completed", "pending")
  using get_transactions(date_range, status).

## Rules
- **ALWAYS** use the available MCP tools — never fabricate business data.
- When querying transactions, use **dynamic date ranges** based on the
  user's request (e.g., "yesterday" → "2026-06-07:2026-06-08").
  If unspecified, default to today's date.
- When querying orders or profiles, extract the **customer ID** from
  the user's query. If no customer ID is provided, ask the user for it
  before making a tool call.
- **Correlate data** across entities when relevant:
  - Link declined transactions to customer profiles.
  - Connect order history with transaction patterns.
  - Identify revenue trends or anomalies.
- Provide **structured business insights** with clear data points.
- Note that PII fields (email, phone) are masked by the MCP server.
"""

# ── Agent Description ────────────────────────────────────────────
BUSINESS_DESCRIPTION = (
    "Handles all business data queries including customer profiles, "
    "order details and history, and transaction analysis filtered by "
    "date range and status. Use this agent for any question about "
    "revenue, sales, customer complaints, payment history, declined "
    "transactions, or business analytics."
)

# ── Agent Definition (Module-Level — Official ADK Pattern) ───────
business_data_agent = Agent(
    model=settings.llm_model,
    name="business_data_agent",
    description=BUSINESS_DESCRIPTION,
    instruction=BUSINESS_INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.mcp_business_url,
            ),
        )
    ],
)