# Session Overview — Fibey Field Ops

> **Conference reference sample for Microsoft Build 2026 — BRK242:**
> *Turn your agents into action: Connect tools, APIs, and documents.*

Fibey Field Ops is a runnable demo of an agent that does real work for
**fiber optics field technicians**. It connects to four very different
backend systems through **one** endpoint — the **Azure AI Foundry Toolbox** —
using a single MCP (Model Context Protocol) connection.

## The scenario

A field technician on a job site needs to:

1. Look up a fiber part — *"Do we have an LC/APC splice tray at the north depot?"*
2. Check or create a work order — *"Open a WO for splice repair at pole 247."*
3. Find a procedure or safety protocol — *"What's the fusion splicing procedure for SMF-28?"*
4. Verify network or service status before cutting over — *"Are we clear to swap the OLT?"*

Each of those is a different system: an MCP inventory server, a FastAPI
work-orders service, an Azure AI Search knowledge base, and a status
dashboard. Wiring all of them directly into one agent would mean four sets
of credentials, four schemas in the prompt, and four code paths to maintain.

## What the Toolbox does for you

The Foundry Toolbox bundles the four tools into a single MCP endpoint with
a consistent interface. The agent sees one tool surface; the Toolbox
dispatches to the right backend.

```text
React UI ──► FastAPI Gateway ──► Fibey Agent ──► Foundry Toolbox (MCP)
                                                      │
                                ┌─────────────────────┼────────────────────┐
                                │                     │                    │
                          Inventory MCP        Work Orders OpenAPI    FoundryIQ KB
                          Container App        Container App          AI Search
```

Benefits demonstrated:

- **One credential, many tools** — single bearer token covers the whole
  Toolbox; individual tools never see the agent's identity.
- **Smaller prompt** — the Toolbox aggregates tool schemas; the agent
  registers one MCP client, not four.
- **Mixed tool types** — the same Toolbox exposes MCP, OpenAPI, and Azure
  AI Search to the agent uniformly.
- **Governance & versioning** — tool inventory and access live in the
  Toolbox config, not in agent code; updating a tool doesn't require
  redeploying the agent.

## Three deployment modes (same agent code)

The sample ships with three execution modes so you can see the same agent
in different runtimes:

| Mode | Where the agent runs | When to use |
|---|---|---|
| `local` | In-process inside the FastAPI gateway | Development, debugging |
| `containerapp` | Standalone Azure Container App | Self-hosted production |
| `hosted` | Azure AI Foundry Agent Service (managed) | Foundry-managed production |

All three speak the same SSE streaming protocol to the React UI.

## What to look at first

1. **`src/fibey/docs/toolbox-integration.md`** — the integration recipe
   (custom `httpx.Auth`, required headers, `api-version=v1`, hosted-mode
   credential chain, MCP SDK quirks). This is the main teaching artifact.
2. **`src/fibey/src/fibey/agent/agent.py`** — local-mode agent + Toolbox
   MCP wiring.
3. **`src/fibey/src/fibey/agent/hosted.py`** — same pattern, but for a
   Foundry-hosted agent with managed identity.
4. **`src/fibey/docs/architecture.md`** — full system diagram, components,
   ports, and streaming protocol.

## Run the sample

See **[`src/fibey/README.md`](../README.md)** for quickstart steps
(`uv sync`, `./scripts/start-dev.sh`) and the per-service launchers under
`services/`.

For an Azure deployment (Container Apps + AI Search + Foundry), see
**[`src/fibey/docs/deployment.md`](./deployment.md)**.
