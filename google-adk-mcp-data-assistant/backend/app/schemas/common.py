from pydantic import BaseModel


class ToolTraceItem(BaseModel):
    server: str
    tool: str
    arguments: dict
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
