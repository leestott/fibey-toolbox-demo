# Architecture

## Overview

Fibey Field Ops is a fiber optics field operations demo built on **Azure AI Foundry Hosted Agents** and the **Foundry Toolbox**. The agent supports field technicians by combining four toolbox-backed operational systems: inventory lookup, work order management, knowledge retrieval, and service-status verification.

## System Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Browser                                                                    │
│  Fibey Field Ops UI                                                        │
│  ┌──────────────────────────────┬───────────────────────────────────────┐  │
│  │ Chat for field technicians   │ Activity sidebar                      │  │
│  │ "Need a splice tray and WO" │ ⚡ inventory-mcp running              │  │
│  │ "Check outage before cutover"│ ✅ work-orders-api complete          │  │
│  └──────────────────────────────┴───────────────────────────────────────┘  │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ POST /api/chat (streaming SSE)
                                ▼
                   ┌──────────────────────────────┐
                   │ Gateway (FastAPI)            │  src/fibey/gateway/
                   │ Azure Container Apps         │
                   └───────────────┬──────────────┘
                                   │ local or hosted agent execution
                                   ▼
                   ┌──────────────────────────────┐
                   │ Fibey Field Ops Agent        │  src/fibey/agent/
                   │ Azure AI Foundry Agent Svc   │
                   └───────────────┬──────────────┘
                                   │ Foundry Toolbox
                                   ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │ Toolbox services                                                │
        │  • inventory-mcp         → parts inventory and stock checks     │
        │  • work-orders-api       → create/view/update work orders       │
        │  • FoundryIQ knowledge   → AI Search + KB MCP retrieval         │
        │  • browser automation    → status dashboard verification        │
        └───────────────┬───────────────────────┬─────────────────────────┘
                        │                       │
          ┌─────────────▼────────────┐  ┌──────▼─────────────────────┐
          │ services/inventory-mcp   │  │ services/work-orders-api   │
          │ Container App / :8001    │  │ Container App / :8002      │
          └──────────────────────────┘  └────────────────────────────┘

          ┌──────────────────────────┐  ┌────────────────────────────┐
          │ services/status-dashboard│  │ services/foundry-iq-docs   │
          │ Static app / :8003       │  │ Blob → Search → KB source  │
          └──────────────────────────┘  └────────────────────────────┘
```

## Components

### Gateway (`src/fibey/gateway/`)

FastAPI API layer between the React UI and the field operations agent.

- **Deployment target**: Azure Container App
- **Endpoints**:
  - `POST /api/chat` — streaming SSE chat endpoint
  - `POST /api/sessions/reset` — clear session state
  - `GET /api/health` — health check
- **Responsibilities**: session management, SSE formatting, routing to local or hosted agent execution

### Agent (`src/fibey/agent/`)

The field operations agent that selects the right toolbox service for the technician's request.

- **Deployment target**: Azure AI Foundry Agent Service
- **Key files**:
  - `agent.py` — agent definition + Toolbox MCP connection
  - `hosted.py` — hosted-mode entrypoint
  - `main.py` — local CLI entrypoint
  - `prompts/system_prompt.md` — field operations system prompt

### Frontend (`ui/`)

React + TypeScript + Tailwind chat experience for field technicians.

- **Deployment target**: Static build served with the gateway or from a static host
- **Key components**:
  - `ChatPanel` — conversation view
  - `MessageBubble` — markdown rendering
  - `ChatInput` — message entry
  - `PromptSuggestions` — clickable starter prompts shown in empty state
  - `ActivitySidebar` — live tool activity feed

### Toolbox services (`services/`)

The `services/` folder contains the operational systems the agent uses:

```text
services/
├── foundry-iq-docs/      # Markdown docs uploaded to blob storage for FoundryIQ
│   └── docs/
├── inventory-mcp/        # MCP server for parts inventory lookup
│   ├── data/
│   └── server.py
├── status-dashboard/     # Static HTML dashboard for network/service status
│   └── public/
└── work-orders-api/      # FastAPI service for work order operations
    ├── data/
    └── server.py
```

#### `services/inventory-mcp/`
- Streamable HTTP MCP server
- Default local port: `8001`
- Provides part search, detail lookup, and stock status checks

#### `services/work-orders-api/`
- FastAPI service for work order CRUD-style operations
- Default local port: `8002`
- Provides work order list, detail, create, and patch endpoints

#### `services/status-dashboard/`
- Static dashboard used by browser automation for network/service checks
- Default local port: `8003`
- Packaged as a lightweight web container

#### `services/foundry-iq-docs/`
- Source markdown files for FoundryIQ knowledge retrieval
- Full retrieval pipeline: Documents → Blob Storage → AI Search Indexer → Index → Knowledge Source → Knowledge Base → MCP endpoint → Foundry connection
- Knowledge sources and knowledge bases are created through the Azure AI Search REST API using `2026-04-01`
- Uploaded to Azure Blob Storage separately from app deployment

## Container Apps topology

The deployment is organized around small, separable services:

| Component | Runtime | Port | Topology |
|-----------|---------|------|----------|
| Gateway | FastAPI | `8080` | Azure Container App handling chat API + UI hosting |
| Inventory MCP | Python MCP server | `8001` | Azure Container App exposed to the Toolbox |
| Work Orders API | FastAPI | `8002` | Azure Container App exposed to the Toolbox |
| Status Dashboard | Static web app | `8003` | Azure Container App or static internal endpoint for browser automation |
| Agent | Azure AI Foundry hosted agent | n/a | Connects to Toolbox and orchestrates tools |
| FoundryIQ docs | Blob storage + Azure AI Search | n/a | Blob-backed content ingested by AI Search, then exposed through a knowledge base MCP endpoint |

## Streaming Protocol

The gateway streams SSE events to the frontend:

```text
event: activity
data: {"tool": "inventory-mcp", "status": "running", "detail": "Checking stock for splice tray..."}

event: delta
data: {"content": "Stock is low at the north depot."}

event: citation
data: {"source": "fiber-splicing-procedures.md", "url": "..."}

event: done
data: [DONE]
```

| Event | Purpose |
|-------|---------|
| `delta` | Assistant text chunk |
| `activity` | Tool invocation status |
| `citation` | Source reference from knowledge tools |
| `error` | Error message |
| `done` | End of stream |

## Agent modes

Controlled by `AGENT_MODE`:

- **`local`** — the gateway runs the agent in-process for local development.
- **`containerapp`** — the gateway proxies (over HTTP/SSE) to a self-hosted
  agent service running as its own Container App
  (`src/fibey/agent/service.py`). This is the recommended production mode.
- **`hosted`** — the gateway proxies to a Foundry-hosted agent
  (`src/fibey/agent/hosted.py`) managed by the Azure AI Foundry platform.

All three modes keep the same UI behavior and streaming contract.
