# Local Development

## Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Azure CLI (for `DefaultAzureCredential` when connecting to Azure services)

## First-Time Setup

```bash
./scripts/setup.sh
```

This will:
1. Run `uv sync` for the root project
2. Install UI dependencies in `ui/`
3. Copy `.env.example` to `.env` if needed

## Running the main app

### Gateway + UI

```bash
./scripts/start-dev.sh
```

Starts:
- Gateway: http://localhost:8080
- UI: http://localhost:5173

### Gateway only

```bash
uv run uvicorn fibey.gateway.api_server:app --reload --port 8080
```

### UI only

```bash
cd ui && npm run dev
```

### Agent CLI

```bash
uv run python -m fibey.agent.main
```

Useful for testing the field operations persona without the browser UI.

## Running toolbox services locally

### Inventory MCP server

```bash
cd services/inventory-mcp
uv sync
uv run python server.py
```

- URL: `http://localhost:8001`
- Use for local inventory lookup and stock-check flows.

### Work Orders API

```bash
cd services/work-orders-api
uv sync
uv run python server.py
```

- URL: `http://localhost:8002`
- Provides `/work-orders` and `/health` endpoints for local testing.

### Status dashboard

You can either open the dashboard directly from disk or serve it locally.

- Open `services/status-dashboard/public/index.html` in a browser, or
- Serve it with a simple HTTP server:

```bash
cd services/status-dashboard/public
python -m http.server 8003
```

- URL: `http://localhost:8003`
- Used by browser automation to verify network/service status.

### FoundryIQ knowledge base content

The markdown documents under `services/foundry-iq-docs/docs/` are **not** served by the local app. Upload them to blob storage and ingest them into FoundryIQ separately.

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_MODE` | No | `local` | `local`, `containerapp`, or `hosted` |
| `FOUNDRY_PROJECT_ENDPOINT` | Hosted/containerapp mode | — | Foundry project endpoint |
| `FOUNDRY_MODEL` | No | `gpt-4.1-mini` | Model deployment name |
| `HOSTED_AGENT_NAME` | Hosted mode | `fibey-agent` | Hosted agent name |
| `CONTAINERAPP_AGENT_URL` | Containerapp mode | — | URL of the deployed agent-service Container App |
| `TOOLBOX_MCP_URL` | For real toolbox access | — | Foundry Toolbox MCP endpoint (without `api-version` — code appends `?api-version=v1`) |
| `AZURE_SEARCH_ENDPOINT` | For direct KB fallback | — | Azure AI Search endpoint |
| `AZURE_SEARCH_INDEX` | For direct KB fallback | `foundry-iq-docs-index` | Search index name |
| `AZURE_SEARCH_API_KEY` | For direct KB fallback | — | Search admin/query key |
| `GATEWAY_HOST` | No | `0.0.0.0` | Gateway bind host |
| `GATEWAY_PORT` | No | `8080` | Gateway bind port |

## Testing the gateway API

```bash
curl http://localhost:8080/api/health

curl -N -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check splice tray stock", "session_id": "test-1"}'

curl -X POST http://localhost:8080/api/sessions/reset \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-1"}'
```

## Project Structure

```text
src/
└── fibey/
    ├── agent/            # Field operations agent and prompts
    └── gateway/          # FastAPI chat gateway

services/
├── foundry-iq-docs/      # Markdown content for FoundryIQ ingestion
├── inventory-mcp/        # Parts inventory MCP server
├── status-dashboard/     # Static service-status dashboard
└── work-orders-api/      # FastAPI work order service

ui/
└── src/                  # React frontend
```
