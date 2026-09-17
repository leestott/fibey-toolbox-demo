# Develop the Fibey sample locally

Local development runs the gateway and UI on your workstation while using a configured Microsoft Foundry project, model, and toolbox. It is useful for inspecting agent behavior without rebuilding the hosted image on every change, but it still makes Azure calls and can mutate synthetic work orders.

The local servers do not provide the cloud UI's Entra authentication boundary. Use synthetic data, bind listeners to loopback, and never treat a development server as a protected public deployment. Follow [the deployment guide](../deployment_guide.md) for the hosted solution.

## Configure the local environment

Use Python 3.12+, uv, Node.js 24 LTS, and Azure CLI. The repository's dependency locks are the reproducible baseline; do not replace frozen installation with broad package upgrades.

Copy `.env.example` only when you do not already have a local `.env`. Use your own Foundry endpoint and developer identity; downstream inventory/orders API keys belong in Foundry connections, not in the browser or prompt.

```powershell
uv sync --frozen
Copy-Item .env.example .env
az login
```

Edit the ignored `.env`:

| Setting | Local use |
|---|---|
| `AGENT_MODE=local` | Run the agent inside the gateway |
| `FOUNDRY_PROJECT_ENDPOINT` | Actual project endpoint |
| `FOUNDRY_MODEL=gpt-5.4-mini` | Your configured model deployment name |
| `TOOLBOX_MCP_URL` | Configured consumer or version-specific MCP endpoint; `api-version=v1` is accepted |
| `SKILLS_SOURCE=file` | Optional deterministic rehearsal using the five bundled skills |
| `CORS_ORIGINS` | Exact origins if needed; leave empty for Vite's same-origin proxy |

For local testing of the hosted route, use `AGENT_MODE=hosted`, `HOSTED_AGENT_ENDPOINT=<project-endpoint>`, and `HOSTED_AGENT_NAME=fibey-agent` with a developer identity authorized to invoke it. `containerapp` and `fibey.agent.service` are optional legacy/local adapters, not the current hosted deployment.

## Start the gateway and UI

The development gateway listens on port 8080, while the cloud gateway container uses port 8000. Vite serves the UI on port 5173 and proxies `/api` to the local gateway.

Use separate terminals so that you can observe gateway errors and frontend output independently. Nginx's `GATEWAY_HOST` and `GATEWAY_URL` are deployed-UI upstream settings, not local gateway bind controls.

From the repository root:

```powershell
uv run --frozen uvicorn fibey.gateway.api_server:app --host 127.0.0.1 --port 8080
```

In another terminal:

```powershell
Set-Location ui
npm ci
npm run dev
```

Open <http://localhost:5173>. For a terminal-only conversation, run `uv run --frozen python -m fibey.agent.main` from the root.

## Exercise the chat contract

The chat API accepts a nonempty message of at most 16,000 characters and a UUID session ID. The UUID is a conversation handle, not proof of user identity. Use the same value for follow-up turns and reset.

Start with a health request, then a synthetic tool request. Server-sent events (SSE) report text, activity, citations, failures, and termination. A healthy gateway alone does not prove that the remote toolbox works.

```powershell
$base = "http://127.0.0.1:8080"
Invoke-RestMethod "$base/api/health"
```

Send one conversation turn:

```powershell
$session = [guid]::NewGuid().ToString()
$body = @{ message = "Show me WO-007."; session_id = $session } | ConvertTo-Json -Compress
$response = Invoke-WebRequest "$base/api/chat" -Method Post -ContentType "application/json" -Body $body
$response.Headers["X-Session-Id"]
$response.Content
```

This command prints the completed SSE body; use the browser to see incremental streaming. For reusable follow-up calls in the same PowerShell session:

```powershell
function Invoke-FibeyTurn {
    param([string] $Message, [string] $SessionId)
    $payload = @{ message = $Message; session_id = $SessionId } | ConvertTo-Json -Compress
    $result = Invoke-WebRequest "$base/api/chat" -Method Post `
        -ContentType "application/json" -Body $payload
    return $result.Content
}
Invoke-FibeyTurn -Message "What parts does that work order need?" -SessionId $session
```

Reset after the active response finishes:

```powershell
$reset = @{ session_id = $session } | ConvertTo-Json -Compress
Invoke-RestMethod "$base/api/sessions/reset" -Method Post -ContentType "application/json" -Body $reset
```

Reset clears chat context, not work orders. An overlapping turn or reset returns 409; malformed/non-UUID inputs fail validation. A truncated upstream stream must surface an error instead of hanging.

## Work with supporting services

The normal local agent still calls a cloud toolbox and its reachable services. A cloud-hosted toolbox cannot connect to `localhost` on your workstation; running a local inventory server does not automatically replace its configured cloud connection.

For direct service development, install from each service's existing lock and bind explicitly to loopback. These local listeners may have API-key enforcement disabled unless configured; never expose them publicly as a shortcut.

| Component | Local approach |
|---|---|
| Inventory MCP | Use the existing service tests or a deliberate local MCP client setup; `server.py`'s direct launcher binds all interfaces, so do not expose it on a shared network |
| Work-orders API | From `services\work-orders-api`, use `uv sync --frozen` then `uv run --frozen uvicorn server:app --host 127.0.0.1 --port 8002` |
| Status dashboard | From `services\status-dashboard\public`, use `python -m http.server 8003 --bind 127.0.0.1`; inventory reads its configured `STATUS_DASHBOARD_URL` |
| Knowledge documents | Markdown is ingested into Blob/Search by `scripts\setup-knowledge-base.ps1`, not served by the local UI |

The dashboard is an HTML data source for the narrow status tool, not browser automation. Work-order data is loaded from its seed JSON and kept in memory; a service restart discards updates.

## Run the existing checks

The repository includes standard-library Python regression tests covering runtime, gateway, and tool-service behavior. The frontend build includes TypeScript checking.

Use these commands before changing the hosted runtime or shared tool contracts. They do not replace target-environment authorization and tool-execution acceptance checks.

```powershell
uv run --frozen python -m unittest discover -s tests -p "test_*.py"
Set-Location ui
npm run build
```

For failure diagnosis, see [toolbox integration](toolbox-integration.md#diagnose-by-boundary) and [deployment troubleshooting](../deployment_guide.md#diagnose-failures-by-boundary). Keep sensitive telemetry disabled and avoid logging messages or tool payloads.
