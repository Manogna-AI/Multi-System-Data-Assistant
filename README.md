# Google ADK + MCP — Multi-System Data Assistant

Production-oriented local prototype of a React + FastAPI chatbot that routes enterprise questions through a Google ADK-style root agent and specialist agents. External data access is constrained to exactly three MCP servers: observability, business data, and controlled action.

## A. Final production-ready folder structure

The generated project lives in `google-adk-mcp-data-assistant/` and contains `backend/` and `frontend/` applications matching the requested layout.

## B. Major folders and files

- `backend/app/api`: FastAPI route modules for chat, health, MCP registry, and audit.
- `backend/app/agents`: Root/orchestrator/specialist agent modules. Agents call MCP toolset wrappers only.
- `backend/app/mcp_clients`: ADK-compatible MCP toolset wrappers. They build Google ADK `McpToolset` objects when the package is available.
- `backend/mcp_servers`: Exactly three FastMCP servers with safe typed tools.
- `backend/app/data`: Mock telemetry, business, and action audit data only.
- `frontend/src`: Vite React chatbot UI with tool trace and action confirmation panels.

## C-D. Backend and MCP code

See source files under `backend/app` and `backend/mcp_servers`. MCP tools expose only the requested typed functions and enforce allowlists, enums, masking, window limits, and action confirmation.

## E. Frontend code

See `frontend/src`. The UI calls only the FastAPI backend using `VITE_API_BASE_URL`; it never sees secrets.

## F. Environment variables

Copy `backend/.env.example` to `backend/.env` and set model/provider variables as needed. Do not commit secrets.

Frontend may use:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## G. How to run MCP servers

From `google-adk-mcp-data-assistant/backend` after installing requirements:

```bash
python -m mcp_servers.observability_server
python -m mcp_servers.business_data_server
python -m mcp_servers.action_server
```

Run each command in a separate terminal.

## H. How to run backend

```bash
cd google-adk-mcp-data-assistant/backend
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell: . .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## I. How to run frontend

```bash
cd google-adk-mcp-data-assistant/frontend
npm install
npm run dev
```

## J. Test commands

```bash
cd google-adk-mcp-data-assistant/backend
pytest
```

## K. Production-readiness checklist

- Agents do not import mock data and delegate to MCP toolsets.
- MCP servers expose exactly three domain-specific server modules.
- Action tools require `confirm=True` and log accepted/rejected attempts.
- Business profile responses mask email and phone.
- Validation covers services, time ranges, date ranges, customer IDs, statuses, priorities, replicas, and confirmation.
- No secrets are hardcoded.
- No arbitrary command tool is exposed by the MCP servers.

## L. Known extension points

- Replace mock data modules with real connectors inside MCP servers only.
- Add authentication/authorization at FastAPI and MCP boundaries.
- Deploy MCP servers independently and make tool wrappers use remote streamable HTTP exclusively.
- Add richer ADK runners, sessions, and evals around the existing agent boundaries.
