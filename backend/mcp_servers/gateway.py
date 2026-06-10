"""
🚀 MCP Gateway — Unified entry point for all MCP servers.

Composes all 3 domain MCP servers into a single FastMCP instance
using the official mount() composition pattern.

All 9 tools are exposed on a SINGLE endpoint:
  http://localhost:8010/mcp

Architecture Mapping:
  ADK Agents → McpToolset → http://localhost:8010/mcp → Gateway
    Gateway routes to:
      🔵 Observability tools (get_logs, get_metrics, get_alerts)
      🟢 Business Data tools (get_orders, get_transactions, get_customer_profile)
      🔴 Action tools (restart_service, create_ticket, scale_service)

References:
  - FastMCP Composition: https://fastmcp.wiki/en/servers/composition
  - FastMCP: https://gofastmcp.com
"""

from fastmcp import FastMCP

# ── Import the 3 domain server instances ─────────────────────────
from mcp_servers.observability_server import mcp as observability_mcp
from mcp_servers.business_data_server import mcp as business_mcp
from mcp_servers.action_server import mcp as action_mcp

# ── Create the unified gateway ───────────────────────────────────
gateway = FastMCP("mcp-gateway")

# ── Mount all 3 servers (no namespace = tools keep original names) ─
gateway.mount(observability_mcp)   # get_logs, get_metrics, get_alerts
gateway.mount(business_mcp)        # get_orders, get_transactions, get_customer_profile
gateway.mount(action_mcp)          # restart_service, create_ticket, scale_service

# ── Server Entry Point ───────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 MCP Gateway starting on http://127.0.0.1:8010/mcp")
    print("   🔵 Observability: get_logs, get_metrics, get_alerts")
    print("   🟢 Business Data: get_orders, get_transactions, get_customer_profile")
    print("   🔴 Action:        restart_service, create_ticket, scale_service")
    print("   ─────────────────────────────────────────────────────")
    gateway.run(transport="streamable-http", host="127.0.0.1", port=8010, path="/mcp")