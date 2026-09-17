# Copilot Instructions — Fibey Field Ops

Fibey is a synthetic fiber-operations demo with an activity sidebar, five instruction skills, and a Foundry toolbox. Preserve its teaching value while keeping the protected deployment boundaries explicit.

`azure.yaml` is authoritative. It defines a Foundry project, GPT-5.4-mini hosted agent using Responses `2.0.0`, and five supporting ACA services. The unused standalone `agent.yaml` has been removed; do not recreate competing deployment definitions.

## Architecture and access

The browser signs in through the Entra-protected, user-allowlisted UI. Nginx proxies to the internal gateway, which invokes the Foundry-hosted agent. Gateway and dashboard are internal ACA services; inventory and work orders are external, API-key-protected services.

The deployment is not production-grade: gateway history mappings and synthetic work orders are in memory and use one replica. There is no enforced human approval UI. Do not claim approval, durability, per-user session authorization, or full network-isolation guarantees that are not implemented.

```text
Entra user → UI → internal gateway → Foundry hosted agent → Foundry Toolbox
                                                        ├─ Inventory MCP → internal status dashboard
                                                        ├─ Work Orders OpenAPI
                                                        └─ Foundry IQ / Search knowledge base
```

- Inventory MCP is stateless Streamable HTTP. Its narrow `get_network_status` tool reads a configured dashboard URL; this is **not browser automation**.
- Work orders are synthetic and reset on a service restart. Chat reset does not reset work orders.
- Foundry connections store inventory/work-order credentials. Never put API keys in prompts, UI code, or checked-in configuration.
- The UI's upstream comes only from `GATEWAY_HOST` and `GATEWAY_URL=https://<host>/api/`.

## Repository and validation

Keep agent logic in `src/fibey/agent/`, gateway logic in `src/fibey/gateway/`, and frontend code in `ui/`. Prompts and skills remain bundled with the agent.

Use the existing dependency locks and test/build commands. Do not replace frozen dependencies with broad unpinned installation or add test libraries unnecessarily.

```powershell
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -p "test_*.py"
```

For local development, copy `.env.example`, supply a real Foundry project/model/toolbox and developer credentials, then start the gateway on loopback:

```powershell
uv run --frozen uvicorn fibey.gateway.api_server:app --host 127.0.0.1 --port 8080
```

The terminal agent is `uv run --frozen python -m fibey.agent.main`. In `ui/`, use `npm ci`, `npm run dev`, or `npm run build`; Vite proxies `/api` to port 8080. Local servers do not provide the cloud Entra boundary.

## Runtime contracts

Hosted mode uses the supported `FoundryToolbox` and `ResponsesHostServer.run_async()` APIs, including runtime call-ID forwarding and scoped Azure credentials. Keep resources closed on both success and failure.

Preserve the SSE activity sidebar, UUID session headers, bounded input validation, exact configured CORS, terminal response handling, and errors for truncated streams. Never log user messages or tool payloads by default.

- `AGENT_MODE=hosted` is the cloud path; `local` is in-process development.
- `containerapp` and `fibey.agent.service` are legacy/local options, not part of the five-service deployment.
- Hosted skills use SDK MCP discovery with bundled-file fallback; explicit `mcp` mode fails if published skills are unavailable.
- Read-only skill loading is unattended; this does not enforce approval for operational writes.
- Keep OpenTelemetry enabled, sensitive content off unless `ENABLE_SENSITIVE_TELEMETRY=true`.
- Do not globally monkeypatch MCP validation or silently discard failed history retrieval.

## Deployment workflow

Follow `docs/deployment.md` from the demo root. Provision the `foundry` layer, configure aliases and protected-service prerequisites, then run `azd provision infra` for placeholder apps on port 80 with explicit system-identity registry links. Verify every supporting app's `AcrPull` role and the remaining build/push/resource roles.

Use `azd publish <service>` for status-dashboard, inventory-mcp, work-orders-api, gateway, and ui. Once all five `SERVICE_*_IMAGE_NAME` settings exist, run `azd provision infra` again to apply images with actual ports/probes. Plain `azd deploy` preserves placeholder port 80 and must not be used for the initial supporting-service switch. Verify revisions, run `scripts/setup-knowledge-base.ps1` then `scripts/setup-toolbox.ps1`, and finally run `azd deploy fibey-agent`. Do not run initialization/scaffolding over an existing environment or use obsolete all-in-one deployment instructions.

Keep target subscription, region, project, and endpoints environment-specific. Report which resources and access checks are actually verified; partial provisioning is not evidence that the full demo is live.
