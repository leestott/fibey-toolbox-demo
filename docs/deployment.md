# Deploy the protected Fibey demo

This guide takes the local demonstration to Microsoft Foundry and Azure Container Apps (ACA). Foundry hosts the agent; ACA hosts the UI, gateway, inventory MCP, work-orders API, and status dashboard. `azure.yaml` is authoritative, including the GPT-5.4-mini deployment and Responses protocol version `2.0.0`.

**Deployed 2026-09-17:** The approved `ai-team` / `northcentralus` environment has five running supporting apps, hosted agent version 1, toolbox version 5, and eight indexed knowledge documents. Live tool calls and a combined hosted briefing succeeded. UI nginx-to-gateway streaming, follow-up context, and reset also succeeded. Anonymous UI access redirects to Entra; interactive sign-in requires the allowlisted user's browser session.

## Understand the access boundaries

The public UI requires Microsoft Entra login and an explicit allowed-user object ID. Its gateway and the status dashboard use internal ACA ingress, so users should not browse those endpoints directly.

The two operational APIs need external ingress for the Foundry toolbox, but they require API keys. Keys live in ACA secrets and Foundry connection credentials, never in the UI, prompt, or checked-in toolbox definition.

| Component | Hosting and access |
|---|---|
| UI | External ACA; Entra authentication and allowlisted user |
| Gateway | Internal ACA; `AGENT_MODE=hosted`; one replica |
| Inventory MCP | External ACA; `x-api-key`; stateless Streamable HTTP MCP |
| Work-orders API | External ACA; `x-api-key`; one replica with synthetic in-memory data |
| Status dashboard | Internal ACA; accessed only by inventory's `get_network_status` |
| Fibey agent | Foundry hosted container; Responses 2.0; GPT-5.4-mini |
| Knowledge retrieval | Azure AI Search index, knowledge source, and knowledge base |
| Images and telemetry | ACR, Log Analytics, and configured Foundry telemetry |

There is no browser-automation service and no ACA-hosted agent service in this deployment. The work-order tools do not enforce a human approval step.

## Prepare an isolated environment

Use current Azure CLI, PowerShell 7.2+, and `azd` meeting `azure.yaml`'s minimum version. The installed Foundry extensions must provide `azure.ai.project`, `azure.ai.agent`, connection creation, toolbox deployment, and toolbox publishing. Check local `--help` output before proceeding if the extension commands differ.

The operator needs permission to provision resources, configure the Entra app, build/push images, create Foundry connections, and assign the required scoped roles. Contributor alone does not grant role-assignment permissions. Keep credentials in ignored local configuration or a secret store, and disable shell transcripts/debug output while handling them.

Authenticate, then create or select the intended azd environment from this demo directory:

```powershell
azd auth login
azd env new "<environment-name>"
```

Sign in to Azure CLI as well for the setup scripts. Configure the target subscription by GUID and region before provisioning:

```powershell
azd env set AZURE_SUBSCRIPTION_ID "<subscription-guid>"
azd env set AZURE_LOCATION "northcentralus"
```

For the current rollout, the approved project is `leestott-mcpchennai` in subscription `ai-team`, resource group `rg-leestott-mcpchennai`. These are rollout details, not reusable defaults. Use the project and resource-group prompts/settings for your chosen environment; do not import another demo's account URL.

## Provision Foundry and placeholder infrastructure

The Foundry layer creates the project, model deployment, and registry used by the hosted agent. The supporting Bicep layer needs those outputs, as well as the Entra and API-key settings, before it can be provisioned correctly.

The GPT-5.4-mini GlobalStandard allocation is capacity 100 (100,000 tokens and 100 requests per minute for this deployment). Capacity 10 caused rate-limit failures during multi-tool briefings. Check available quota before provisioning, and keep `azure.yaml` and `infra/foundry/main.parameters.json` aligned when changing capacity. This is a throughput allocation, not prepaid token usage; inference and other Azure charges still apply.

Run only the Foundry layer first. In an existing environment, confirm the selected environment and its existing outputs before creating anything new:

```powershell
azd provision foundry
```

Read the actual project endpoint produced by provisioning, and establish the runtime aliases:

```powershell
$endpoint = azd env get-value FOUNDRY_PROJECT_ENDPOINT
azd env set HOSTED_AGENT_ENDPOINT $endpoint
azd env set FOUNDRY_MODEL "gpt-5.4-mini"
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME "gpt-5.4-mini"
azd env set TOOLBOX_NAME "fibey-toolbox"
```

Set the toolbox aliases using that same project; registration happens later:

```powershell
$toolbox = "$endpoint/toolboxes/fibey-toolbox/mcp?api-version=v1"
azd env set TOOLBOX_MCP_URL $toolbox
azd env set TOOLBOX_ENDPOINT $toolbox
```

Before provisioning `infra`, supply these values in the selected ignored azd environment:

| Setting | Meaning |
|---|---|
| `UI_CLIENT_ID` | Single-tenant Entra application's client ID |
| `UI_CLIENT_SECRET` | Secret for that application, kept out of source control |
| `AZURE_PRINCIPAL_ID` | Allowed user's Entra object ID, not an application/client ID |
| `INVENTORY_API_KEY` | Random key of at least 32 characters |
| `WORK_ORDERS_API_KEY` | Separate random key of at least 32 characters |
| `AZURE_FOUNDRY_RESOURCE_GROUP` | Foundry layer's resource-group output |
| `AZURE_AI_ACCOUNT_NAME`, `AZURE_AI_PROJECT_NAME` | Foundry layer's account/project outputs |
| `AZURE_CONTAINER_REGISTRY_RESOURCE_ID` | Registry output from the Foundry layer |

Configure the UI application's web redirect URI to `https://<ui-host>/.auth/login/aad/callback` once its actual hostname is known. Do not replace the user allowlist with tenant-wide anonymous or unrestricted access.

```powershell
azd provision infra
```

This is the first phase of the ACA launch. Initial provisioning uses a public placeholder image when a service's `SERVICE_*_IMAGE_NAME` setting is empty. The placeholder listens on port 80 and has no application-specific probes; each app also receives its system-assigned identity and explicit registry association. These placeholders are not the running Fibey applications.

## Publish supporting images, then apply them together

Before publishing, verify `AcrPull` on the registry for all five supporting apps' system-assigned identities and the corresponding pull permission for the Foundry-hosted agent identity. The deployment identity also needs image-build and push permissions. Do not enable the registry's admin password or grant broad subscription roles to work around missing scoped assignments.

**Registry association is a separate requirement from RBAC.** `azd deploy` does not automatically configure the ACA registry-identity link for this stack. Every app module passes the ACR server to `infra/modules/container-app.bicep`, which explicitly sets `configuration.registries` with `server: registryServer` and `identity: 'system'`. Verify that association is present on the deployed app before expecting its system-assigned identity to pull a private image.

Also verify gateway-to-Foundry invocation permission, model/tool access for the hosted identity, and Search/Blob permissions used by knowledge setup. Allow time for new role assignments to propagate.

Publish all five supporting images individually. `azd publish` builds and pushes an image without switching the running ACA revision, keeping the placeholder configuration intact until every image is available:

```powershell
azd publish status-dashboard
azd publish inventory-mcp
azd publish work-orders-api
azd publish gateway
azd publish ui
```

Confirm that all five image outputs exist in the selected azd environment before proceeding:

| Service | Image setting | Real target port |
|---|---|---|
| Status dashboard | `SERVICE_STATUS_DASHBOARD_IMAGE_NAME` | 8003 |
| Inventory MCP | `SERVICE_INVENTORY_MCP_IMAGE_NAME` | 8001 |
| Work-orders API | `SERVICE_WORK_ORDERS_API_IMAGE_NAME` | 8002 |
| Gateway | `SERVICE_GATEWAY_IMAGE_NAME` | 8000 |
| UI | `SERVICE_UI_IMAGE_NAME` | 80 |

Then run the second ACA phase: reapply the supporting infrastructure once to configure the published images and their matching target ports and readiness/liveness probes together:

```powershell
azd provision infra
```

**Do not use plain `azd deploy <supporting-service>` for this initial switch.** It preserves the placeholder `targetPort: 80` rather than changing it to the required ports 8000–8003. Publishing first and provisioning second applies each image with its required infrastructure settings. Preserve all five image settings; an empty setting selects the placeholder again.

Verify each resulting revision and its port/probes before registering tool connections. One infrastructure deployment applies the configuration, but it is not an all-or-nothing rollout or proof that every service is healthy.

Confirm that ACA supplies the UI with `GATEWAY_HOST=<internal-gateway-host>` and `GATEWAY_URL=https://<internal-gateway-host>/api/`. The UI container fails startup if these values are missing or inconsistent; its proxy verifies upstream TLS, supplies SNI, and allows 600-second streams. `proxy_ssl_verify_depth 3` accommodates the ACA certificate chain. Do not disable certificate verification to resolve a proxy 502.

Gateway settings include `AGENT_MODE=hosted`, `HOSTED_AGENT_ENDPOINT=<project-endpoint>`, `HOSTED_AGENT_NAME=fibey-agent`, and `AZURE_TENANT_ID`. `CORS_ORIGINS` accepts exact comma-separated origins; the same-origin UI proxy does not need a wildcard.

## Configure knowledge and tool connections

The knowledge script uploads the bundled Markdown, creates the Search data source/index/indexer, verifies ingestion, and configures the knowledge source, knowledge base, and Foundry connection. It is separate from container deployment because the documents are not container content.

The toolbox script uses the deployed work-orders OpenAPI specification and the configured API keys. It publishes inventory/status, work-order operations, and knowledge retrieval through one toolbox. It does not expose a reset/admin operation as an agent tool.

Run these scripts only after the supporting endpoints, required settings, and roles are ready:

```powershell
pwsh -File .\scripts\setup-knowledge-base.ps1
pwsh -File .\scripts\setup-toolbox.ps1
```

Both accept `-EnvironmentName <name>` and `-CheckOnly`. Check-only validates local configuration and tooling; it is not a cloud reachability or authorization test. Use their built-in checks rather than copying outdated manual Search or connection requests.

The knowledge script uses GA Search object APIs but preview knowledge-base configuration/MCP APIs, with explicit minimal reasoning and extractive output. Retrieval defaults limit results to three documents and 6,000 output tokens. The OpenAPI tool uses `project_connection` authentication with an `x-api-key` connection credential, not a credential named after the `APIKeyHeader` schema identifier.

Finally, deploy the hosted agent:

```powershell
azd deploy fibey-agent
```

`azure.yaml` supplies the model and toolbox settings; Foundry supplies the project/identity context. `python -m fibey.agent.hosted` remains the container entrypoint. The old standalone `agent.yaml` has been removed to avoid two competing deployment definitions.

## Verify before presenting

Check the protected paths before treating the environment as ready. A healthy container or a completed provisioning command does not establish that identity, tool discovery, model access, and streaming all work together.

Use the Entra-protected UI for the normal verification journey, and retain only redacted evidence. Do not paste credentials, session cookies, or full user messages into deployment logs.

1. An unauthenticated UI request must trigger sign-in; a signed-in but non-allowlisted user must be denied.
2. Gateway and dashboard must not have publicly usable external ingress.
3. Inventory and work-order operational endpoints must reject absent/incorrect API keys; health endpoints may remain anonymous for probes.
4. Ask for inventory, a work order, a cited procedure, and network status. Confirm real tool activity rather than guessed answers.
5. Ask a follow-up question and confirm continuity; reset chat and confirm that earlier context is no longer used.
6. Make a synthetic work-order update, verify it, then reset demo data by restarting the single work-orders service from its seed data.
7. Confirm a successful SSE stream ends once, and failed/truncated responses show an error rather than hanging.

## Operate within the demo's limits

The gateway keeps response mappings in process memory and therefore stays at one replica. Work orders are also in memory and reset on a process restart; chat reset and work-order reset are different actions.

Neither this topology nor its UI implements production approval guarantees. Before using real operational data, add durable state, session ownership checks, a real approval workflow, secret rotation, stronger network isolation, and operational recovery controls. Keep sensitive tracing disabled unless explicitly required for a controlled synthetic-data investigation.

The reference UI application's client secret expires on **2027-03-17**. Rotate it in Entra and update the ignored azd `UI_CLIENT_SECRET` setting and ACA configuration before that date. Environment-specific Foundry workflow metadata is kept in ignored `.foundry/agent-metadata.yaml`; it is not a reusable runtime default.

For SDK behavior and tool contracts, see [Toolbox integration](toolbox-integration.md) and the [official hosted-agent documentation](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent).
