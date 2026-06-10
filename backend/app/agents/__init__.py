"""
Agents Package — Google ADK multi-agent system.

Exports:
  - root_agent: Root orchestrator with workflow agents
"""

from app.agents.root_agent import root_agent

__all__ = ["root_agent"]