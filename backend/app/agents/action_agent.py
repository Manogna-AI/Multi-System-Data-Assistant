"""
🔴 Action Agent — Google ADK LlmAgent with MCP Toolset.

Connects to the Action MCP Server (Port 8012) to perform operational
actions like restarting services, scaling replicas, and creating tickets.
All actions REQUIRE explicit user confirmation.

Architecture Mapping:
  ⚙️ Action Agent → McpToolset → Action Server (Port 8012)
  Tools: restart_service, create_ticket, scale_service
  Properties: Confirmation · Allowlist · Logged

CRITICAL SAFETY:
  This agent enforces confirmation guards at the AGENT level.
  The MCP server ALSO enforces allowlist and logging at the TOOL level.

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
ACTION_INSTRUCTION = """You are an **Operations Action** agent.

## Capabilities

You have access to MCP tools that let you:
- **Restart Service** — Restart a specified microservice by name
  using restart_service(service_name, confirm).
- **Scale Service** — Adjust the replica count of a service (scale up/down)
  using scale_service(service_name, replicas, confirm).
- **Create Ticket** — Create an incident or investigation ticket with
  a title, description, and priority level
  using create_ticket(title, description, priority, confirm).

## CRITICAL SAFETY RULES

⚠️ **ALL actions are state-changing and potentially destructive.**

**BEFORE executing ANY tool**, you MUST follow this exact sequence:
- Clearly describe the intended action to the user.
- State the target service name and all parameters.
- Explicitly ask: **"Shall I proceed with this action? (yes/no)"**
- **ONLY** execute the tool if the user confirms with "yes", "confirm",
  "go ahead", or an unambiguous affirmative response.

**If the user has NOT confirmed:**
- Do NOT call any action tools.
- Instead, present the action plan and wait for confirmation.

**After execution:**
- Provide a clear summary of the result.
- Include any relevant details (e.g., ticket ID, new replica count).

## Parameter Extraction
- Extract the **service name** from the user's query.
  If ambiguous or missing, ask the user to specify.
- For scaling, extract the **desired replica count**.
  If unspecified, ask the user.
- For tickets, extract **title**, **description**, and **priority**
  (low/medium/high/critical). If unspecified, propose reasonable
  defaults and confirm with the user before creating.

## OUTPUT RULES
- NEVER reveal internal reasoning, planning steps, or chain-of-thought.
- NEVER include phrases such as:
  - "We can provide answer"
  - "I will now"
  - "Now format"
  - "Analysis:"
  - "Observation:"
- Return only the final user-facing response.
- Keep responses clean, professional, and concise.

## Allowed Services
The MCP server enforces an allowlist. If a service is not in the
allowlist, the tool will return an error. Report this to the user.
"""

# ── Agent Description ────────────────────────────────────────────
ACTION_DESCRIPTION = (
    "Handles all operational actions including restarting services, "
    "scaling service replicas up or down, and creating incident or "
    "investigation tickets. ALL actions require explicit user confirmation "
    "before execution. Use this agent for any request to perform a "
    "system action, create a ticket, or modify infrastructure."
)

# ── Agent Definition (Module-Level — Official ADK Pattern) ───────
action_agent = Agent(
    model=settings.llm_model,
    name="action_agent",
    description=ACTION_DESCRIPTION,
    instruction=ACTION_INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=settings.mcp_action_url,
            ),
        )
    ],
)