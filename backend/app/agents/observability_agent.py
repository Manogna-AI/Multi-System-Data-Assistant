"""
🔵 Observability Agent — Google ADK LlmAgent with MCP Toolset.

Connects to the Observability MCP Server (Port 8010) to query system
telemetry: logs, metrics, and alerts.

Architecture Mapping:
  📊 Observability Agent → McpToolset → Observability Server (Port 8010)
  Tools: get_logs, get_metrics, get_alerts
  Properties: Read-Only · Time Validated · Size Limited

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

OBSERVABILITY_INSTRUCTION = """You are a **System Observability Specialist** agent.

## Available Tools
- get_logs(service_name, start_time, end_time) — service logs
- get_metrics(service_name, metric_name, window) — performance metrics
  Available metrics: error_rate, latency_p95_ms, throughput
- get_alerts(service_name) — active alerts

## Rules
- Use MCP tools only — never fabricate data.
- Default time range: last 24 hours if not specified.
- **Efficiency: Make MINIMAL tool calls.**
  - Query at most 2 services (start with payment-service)
  - Only use metrics: error_rate, latency_p95_ms, throughput
  - Do NOT try cpu_usage, memory_usage (they don't exist)
  - Do NOT repeat a failed metric with different names
- Provide a concise summary with specific numbers.
- Do NOT transfer to another agent.
"""

# ── Agent Description ────────────────────────────────────────────
OBSERVABILITY_DESCRIPTION = (
    "Handles all observability and monitoring queries including system logs, "
    "performance metrics (error_rate, latency, throughput, cpu_usage, "
    "memory_usage), and active alerts for any service. Use this agent for "
    "any question about service health, infrastructure monitoring, error "
    "investigation, or performance analysis."
)

# ── Agent Definition (Module-Level — Official ADK Pattern) ───────
observability_agent = Agent(
    model=settings.llm_model,
    name="observability_agent",
    description=OBSERVABILITY_DESCRIPTION,
    instruction=OBSERVABILITY_INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.mcp_observability_url,
            ),
        )
    ],
)