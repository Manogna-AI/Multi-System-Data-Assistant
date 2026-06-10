"""
FastAPI Application Entry Point — Multi-System Data Assistant.

Architecture Mapping CORS · Port 8001Architecture Mapping:
    📄 Swagger UI — API Documentation (auto-generated at /docs)

This module:
    1. Creates the FastAPI app with CORS middleware
    2. Registers all API routers (health, chat, mcp, audit)
    3. Registers global exception handlers
    4. Verifies Ollama connectivity on startup
    5. Logs MCP server configuration for debugging

References:
    - FastAPI: https://fastapi.tiangolo.com/
    - Architecture: MCP_Multi_System_Data_Assistant_Architecture.pptx
"""

from __future__ import annotations

import logging
import os

import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_audit import router as audit_router
from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_mcp import router as mcp_router
from app.config import get_settings
from app.logging_config import configure_logging
from app.utils.errors import register_exception_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events.

    On startup:
        - Verifies Ollama is reachable and lists available models
        - Logs MCP server configuration
        - Validates critical environment variables

    On shutdown:
        - Logs clean shutdown message
    """
    settings = get_settings()

    # ── Ensure OLLAMA_API_BASE is set ──────────────────────────────
    # LiteLLM relies on this env var for Ollama routing
    # Reference: https://adk.dev/agents/models/ollama/
    if "OLLAMA_API_BASE" not in os.environ:
        os.environ["OLLAMA_API_BASE"] = settings.ollama_base_url
        logger.info("Set OLLAMA_API_BASE=%s", settings.ollama_base_url)

    # ── Windows UTF-8 fix ──────────────────────────────────────────
    if "PYTHONUTF8" not in os.environ:
        os.environ["PYTHONUTF8"] = "1"

    # ── Verify Ollama Connectivity ─────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                logger.info(
                    "✅ Ollama is reachable at %s. Available models: %s",
                    settings.ollama_base_url,
                    models,
                )
            else:
                logger.warning(
                    "⚠️ Ollama returned status %d at %s",
                    resp.status_code,
                    settings.ollama_base_url,
                )
    except Exception as e:
        logger.warning(
            "⚠️ Ollama is NOT reachable at %s — %s. "
            "Agents will fail if Ollama is not running.",
            settings.ollama_base_url,
            str(e),
        )

    # ── Log MCP Server Configuration ──────────────────────────────
    logger.info("MCP Server URLs:")
    logger.info("  🔵 Observability: %s", settings.mcp_observability_url)
    logger.info("  🟢 Business Data: %s", settings.mcp_business_url)
    logger.info("  🔴 Action:        %s", settings.mcp_action_url)


    # ── Log Model Configuration ───────────────────────────────────
    logger.info("LLM Model: %s (Ollama Only)", settings.llm_model)
    #logger.info("Embedding Model: %s", settings.embedding_model)

    logger.info("🚀 %s started successfully", settings.app_name)

    yield  # ── Application runs here ──

    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("🛑 %s shutting down", settings.app_name)


# ── Initialize Settings & Logging ─────────────────────────────────────────
settings = get_settings()
configure_logging(settings.log_level)

# ── Create FastAPI App ────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Multi-System Data Assistant — MCP Architecture. "
        "Google ADK · FastMCP · LiteLLM · Ollama"
    ),
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────────────────
# Allows React frontend (Port 5173/3000) to call FastAPI (Port 8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Exception Handlers ───────────────────────────────────────────────────
register_exception_handlers(app)

# ── Register Routers ─────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(mcp_router)
app.include_router(audit_router)
