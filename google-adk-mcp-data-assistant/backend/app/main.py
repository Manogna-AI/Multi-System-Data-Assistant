from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_audit import router as audit_router
from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_mcp import router as mcp_router
from app.config import get_settings
from app.logging_config import configure_logging
from app.utils.errors import register_exception_handlers

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(mcp_router)
app.include_router(audit_router)
