from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class DomainValidationError(ValueError):
    """Raised when a tool receives invalid domain input."""


class ActionRejectedError(ValueError):
    """Raised when a controlled action is rejected."""


class MCPUnavailableError(RuntimeError):
    """Raised when an MCP toolset is unavailable."""


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(DomainValidationError)
    async def domain_validation_handler(_: Request, exc: DomainValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": "validation_error", "detail": str(exc)})

    @app.exception_handler(ActionRejectedError)
    async def action_rejected_handler(_: Request, exc: ActionRejectedError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"error": "action_rejected", "detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": "schema_validation_error", "detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": "internal_server_error", "detail": str(exc)})