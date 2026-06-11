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
- **Orders by Customer** — Query order details, statuses, and history by customer ID
  using get_orders(customer_id).
- **Order Search** — Retrieve orders filtered by minimum amount, optionally for one
  specific customer, using search_orders(min_amount, customer_id).
- **Transactions** — Analyze transaction data filtered by date range
  and status (e.g., "declined", "completed", "pending")
  using get_transactions(date_range, status).

## Rules
- ALWAYS use the available MCP tools — never fabricate business data.
- When querying transactions, use dynamic date ranges based on the user's request.
- For customer-specific order history, use get_orders(customer_id).
- For broad order filtering requests such as "orders above 100", use
  search_orders(min_amount, customer_id).
- Only ask for customer_id when it is truly required for the request.
- Correlate data across entities when relevant:
  - Link declined transactions to customer profiles.
  - Connect order history with transaction patterns.
  - Identify revenue trends or anomalies.
- Note that PII fields (email, phone) are masked by the MCP server.

## FINAL RESPONSE RULES
- Return ONLY the final user-facing answer.
- NEVER reveal internal reasoning, planning steps, or scratch analysis.
- NEVER include phrases such as:
  - "We need to"
  - "The user didn't specify"
  - "According to tool usage rules"
  - "We don't have a tool"
  - "We can provide answer"
  - "Now format with markdown table"

## RESPONSE STYLE
- Keep clarification messages short and clear.
- If clarification is needed, respond exactly like this format:

## Clarification Needed

Please provide the missing input needed to continue.

- If the request cannot be completed with available tools, respond exactly like this format:

## Tool Limitation

I don't have the required tools to answer that directly.

- If search_orders returns found=false and includes available amount guidance,
  clearly mention the available order amount range and the nearest available amount.
- For successful answers, use clean markdown tables and concise findings.
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