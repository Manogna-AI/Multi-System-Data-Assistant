"""
Root Agent — Google ADK LlmAgent with sub_agents + direct MCP tools.

Architecture:
  root_agent (LlmAgent)
    ├── tools: All 9 MCP tools (for cross-domain queries)
    └── sub_agents:
          ├── observability_agent  (single-domain OBSERVE)
          ├── business_data_agent  (single-domain BUSINESS)
          └── action_agent         (single-domain ACTION)

  Single-domain: root transfers to sub-agent → sub-agent answers
  Cross-domain:  root calls MCP tools directly → root synthesizes

References:
  - LlmAgent: https://adk.dev/agents/llm-agents/
  - McpToolset: https://adk.dev/tools-custom/mcp-tools/
  - Multi-Agent: https://adk.dev/agents/routing/
"""

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)

from app.agents.observability_agent import observability_agent
from app.agents.business_agent import business_data_agent
from app.agents.action_agent import action_agent
from app.config import get_settings

settings = get_settings()

# ── Root Agent Instruction ───────────────────────────────────────
ROOT_INSTRUCTION = """You are a **Senior Multi-System Data Analyst Assistant**.

You have TWO modes of operation:

## MODE 1: DELEGATE (Single-Domain Queries)

If the user asks about ONLY ONE domain, TRANSFER to the appropriate sub-agent:

| Domain | Sub-Agent | Example Queries |
|---|---|---|
| System monitoring | observability_agent | "Show logs for payment-service", "Get alerts", "Error rate for orders-service" |
| Business data | business_data_agent | "Get orders for CUST-001", "Show declined transactions", "Customer profile" |
| Operational actions | action_agent | "Restart payment-service", "Create a ticket", "Scale checkout-service" |

## MODE 2: INVESTIGATE (Cross-Domain Queries)

If the query needs data from MULTIPLE systems, DO NOT transfer.
Instead, call the MCP tools DIRECTLY yourself, then write a comprehensive answer.

**When to use Mode 2:**
- "Why did revenue drop?" → needs transactions + system errors
- "What is the business impact of payment-service errors?" → needs errors + transactions
- "Show me customer complaints and related logs" → needs customer data + logs
- "Correlate system errors with revenue" → needs both domains
- Any query with: "why", "impact", "root cause", "correlate", "caused"

**Your available tools:**
- get_logs(service_name, start_time, end_time) — system logs
- get_metrics(service_name, metric_name, window) — metrics (error_rate, latency_p95_ms, throughput)
- get_alerts(service_name) — active alerts
- get_orders(customer_id) — customer orders for a single customer
- search_orders(min_amount, customer_id) — orders filtered by minimum amount, optionally for one customer
- get_transactions(date_range, status) — transactions by date and status
- get_customer_profile(customer_id) — customer profile (PII masked)

**Cross-domain investigation steps:**
1. Call business tools first (transactions, orders)
2. Call observability tools (logs, alerts, metrics)
3. Synthesize everything into ONE structured response

## RESPONSE FORMAT (for ALL responses)

Always respond in clean, professional markdown:

### For data queries, use tables:
| Column 1 | Column 2 | Column 3 |
|---|---|---|
| data | data | data |

### For analysis, use this structure:

## [Clear Title]

### 📊 Data Summary
[Table with key data points]

### 🔍 Analysis
[Bullet points explaining findings, correlations, patterns]

### 🎯 Recommendations
[Numbered action items]

## STRICT RULES
- ALWAYS use markdown tables when presenting data (transactions, orders, metrics, alerts)
- ALWAYS include specific numbers, amounts, timestamps from tool results
- NEVER fabricate data — only use what tools return
- NEVER show your thinking process — only the final answer
- NEVER include meta-commentary or planning text such as:
  - "We can provide answer"
  - "Now format with markdown table"
  - "Analysis:"
  - "Observation:"
  - "Let me analyze"
  - "I will now"
  - "The user didn't specify"
- Start response with ## heading — no preamble
- For cross-domain: highlight correlations between business data and system issues
- For actions: ALWAYS transfer to action_agent (it handles confirmation)
- Even when a sub-agent is used, the response shown to the user must be clean, polished, and user-facing
- Do NOT expose raw sub-agent reasoning, planning text, or draft wording
- If clarification is needed, keep it short and use:
  - `## Clarification Needed`
- If the available tools cannot answer the request, keep it short and use:
  - `## Tool Limitation`

"""

ROOT_DESCRIPTION = (
    "Root orchestrator that delegates single-domain queries to sub-agents "
    "and directly investigates cross-domain queries using MCP tools. "
    "Provides structured responses with markdown tables and analysis."
)

# ── Root Agent Definition ────────────────────────────────────────
root_agent = Agent(
    model=settings.llm_model,
    name="data_analyst_assistant",
    description=ROOT_DESCRIPTION,
    instruction=ROOT_INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.mcp_observability_url,
            ),
        ),
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.mcp_business_url,
            ),
        ),
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.mcp_action_url,
            ),
        ),
    ],
    sub_agents=[
        observability_agent,
        business_data_agent,
        action_agent,
    ],
)