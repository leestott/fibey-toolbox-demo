# Deploy and operate the Fibey hosted solution

This guide deploys the synthetic Fibey field-operations assistant to Microsoft Foundry and Azure Container Apps (ACA). Foundry hosts the agent; ACA hosts the UI, gateway, inventory MCP service, work-orders API, and status dashboard. Follow the [engineering architecture](docs/architecture.md) alongside the commands to understand which resource and access boundary each step establishes.

Run commands from the repository root in PowerShell 7.2+. `azure.yaml` is authoritative for the Foundry project, GPT-5.4-mini model, Responses `2.0.0` hosted agent, and five supporting services. This guide replaces environment-specific demonstration instructions: no subscription, project, endpoint, identity, or previous deployment result is a reusable default.

> **Protected demo, not a production system:** Work orders and gateway mappings are in memory. There is no enforced write-approval UI or per-user session authorization. Use synthetic data and an isolated environment. Review the current availability, quota, cost, and preview terms of the services before provisioning.

## Prerequisites and deployment decisions

First choose the target subscription, tenant, supported region, and environment name. Keep Foundry, model availability, hosted-agent support, and service quotas aligned. The configured model is GPT-5.4-mini, model version `2026-03-17`, GlobalStandard capacity `100`; capacity is a throughput allocation, not prepaid inference or guaranteed application throughput.

Separate the permissions to deploy infrastructure from the permissions to use its data. Contributor does not grant role-assignment rights, and successfully creating a resource does not prove model invocation, image pull, or document retrieval works.

| Requirement | Prepare before deployment |
|---|---|
| Tooling | Azure CLI, PowerShell 7.2+, `azd >=1.34.0`, and the `azure.ai.agents` extension version required by `azure.yaml` (`>=1.0.0-beta.9`) |
| Extension capabilities | Project/hosted-agent provisioning plus `azd ai connection create`, `azd ai toolbox deploy`, and `azd ai toolbox publish` |
| Local checks | Python 3.12+, uv, Node.js 24 LTS; use existing dependency locks |
| Azure access | Resource provisioning permissions at the intended scope and permission to create the required scoped role assignments |
| Image builds | Operator permission to submit remote ACR builds and publish images; separate runtime pull permissions |
| Entra application | Single-tenant web application/client ID, client secret, and allowed user's object ID; app registration is not created by supporting Bicep |
| API credentials | Two distinct random keys, each at least 32 characters, for inventory and work orders |
| Budget | Model inference, hosted compute, ACR builds/storage, ACA, Search, Blob Storage, and log ingestion/retention all incur charges |

If a model capacity change is necessary, review both `azure.yaml` and `infra/foundry/main.parameters.json`; keep them aligned. Multi-tool briefings consume more tokens and requests than a single lookup. Do not silently change regions, subscriptions, or model versions to work around a quota failure.

Store credentials only in ignored local azd configuration or an approved secret store. Disable shell transcripts, tracing, and CLI debug logging while handling secrets. Do not print all environment values into a build log, put keys in prompts, or commit `.env`, `.azure/`, or `.foundry/` metadata.

## Select the environment and provision Foundry

Authenticate both command-line tools: the deployment uses azd and the setup scripts also use Azure CLI. Creating an environment is a first-time action; for an existing deployment, select its environment instead of rerunning initialization or scaffolding.

The following commands establish the target, then provision only the Foundry layer. Check the selected subscription before any write and stop on an error rather than continuing with missing or stale outputs.

```powershell
az login
azd auth login
```

For a new deployment:

```powershell
azd env new "<environment-name>"
azd env set AZURE_SUBSCRIPTION_ID "<subscription-guid>"
azd env set AZURE_LOCATION "<supported-region>"
az account set --subscription "<subscription-guid>"
```

For an existing deployment, use `azd env select "<environment-name>"` and select the matching Azure CLI subscription. Inspect `azd env get-value AZURE_SUBSCRIPTION_ID` and `az account show --query "{subscription:id,tenant:tenantId}"` before proceeding.

```powershell
azd provision foundry
```

Read the actual project endpoint from provisioning and set the runtime aliases:

```powershell
$endpoint = azd env get-value FOUNDRY_PROJECT_ENDPOINT
azd env set HOSTED_AGENT_ENDPOINT $endpoint
azd env set FOUNDRY_MODEL "gpt-5.4-mini"
azd env set AZURE_AI_MODEL_DEPLOYMENT_NAME "gpt-5.4-mini"
azd env set TOOLBOX_NAME "fibey-toolbox"
```

Initialize the toolbox URL in the same project; the endpoint will not be ready until registration later in the guide:

```powershell
$toolbox = "$endpoint/toolboxes/fibey-toolbox/mcp?api-version=v1"
azd env set TOOLBOX_MCP_URL $toolbox
azd env set TOOLBOX_ENDPOINT $toolbox
```

The setup script publishes a toolbox version and saves this consumer endpoint. Record the published version during a release; enumeration and execution must be verified after a change. A version-specific developer endpoint can test an immutable version before promotion; do not assume a URL change alone updates every consumer or cached tool schema.

## Configure protected services and create placeholders

Before provisioning the supporting layer, supply the Entra application and operational API secrets in the selected ignored azd environment. The UI client ID is an application identifier; `AZURE_PRINCIPAL_ID` is the allowed human user's object ID, not that application ID.

The supporting Bicep uses the allowed-user principal for the demo operator's Search and Blob data roles as well. If a separate CI/deployment identity runs the setup scripts, it needs its own appropriately scoped permissions; changing the UI allowlist is not a substitute for granting that identity access.

| Setting | Value or source |
|---|---|
| `UI_CLIENT_ID`, `UI_CLIENT_SECRET` | Single-tenant Entra web application's ID and secret |
| `AZURE_PRINCIPAL_ID` | Allowed user's Entra object ID |
| `INVENTORY_API_KEY`, `WORK_ORDERS_API_KEY` | Distinct random values of at least 32 characters |
| `AZURE_FOUNDRY_RESOURCE_GROUP` | Foundry layer's resource-group output |
| `AZURE_AI_ACCOUNT_NAME`, `AZURE_AI_PROJECT_NAME` | Actual Foundry account and project outputs |
| `AZURE_CONTAINER_REGISTRY_RESOURCE_ID` | Registry resource ID from the Foundry layer |
| `AZURE_TENANT_ID` | Intended tenant; verify the deployed gateway and UI auth configuration agree |

Do not enable the ACR admin password or Foundry/Search account keys to bypass identity failures. The declared Foundry account, Search, and document storage disable their respective local/shared-key authentication paths.

```powershell
azd provision infra
```

This creates five supporting apps with system-assigned identities and registry associations. When a `SERVICE_*_IMAGE_NAME` setting is empty, the module uses a public placeholder image on port 80 and omits application-specific probes. These are **not yet the running Fibey applications**.

Once the actual UI hostname is known, configure the Entra application's web redirect URI as `https://<ui-host>/.auth/login/aad/callback`. Keep the explicit allowed-user object ID. Do not broaden access to everyone in the tenant merely to get past sign-in.

## Verify RBAC and image-pull boundaries

Role-based access control (RBAC) is scoped to an identity and resource, not inherited from a successful browser login. Inspect the assignments declared in `infra/modules/access.bicep` and the Foundry modules, then verify their effective presence in the target environment. New assignments can take time to propagate.

There are two independent image-pull requirements: a role granting registry access and an ACA registry association choosing the identity used for that access. The app module sets `configuration.registries` with the registry server and `identity: system`; verify both before publishing and switching images.

| Principal | Scope and declared/required access |
|---|---|
| All five ACA system identities | Declared `AcrPull` on the selected ACR |
| Foundry project managed identity | Declared registry pull role when the Foundry ACR is provisioned; verify the project registry connection |
| Gateway managed identity | Declared Azure AI User (`53ca6127-db72-4b80-b1b0-d745d6d5456d`) on the Foundry project |
| Foundry project managed identity | Declared Search Index Data Reader (`1407120a-92aa-4202-b7e9-c0e197c71c8f`) on Search |
| Search managed identity | Declared Storage Blob Data Reader on the document storage account |
| Configured demo operator/user | Declared Search Service Contributor, Search Index Data Contributor, and Storage Blob Data Contributor on the corresponding services |
| Configured Foundry developer principal | Foundry template declares Cognitive Services User on the project when a principal is supplied; verify effective connection/toolbox authoring permissions separately |
| Deployment/build operator | Requires resource and role-assignment permissions, remote-build/image-push rights, and Foundry connection/toolbox writes; do not assume these are all provisioned |
| Hosted agent runtime identity | Verify model and toolbox access in Foundry; distinct from the project identity used by the Search connection and image infrastructure |

### Inspect one app, then repeat for all five

Use an actual app name returned by the deployment. The read-only commands below show a selected identity and ingress without dumping secret values:

```powershell
$group = azd env get-value AZURE_RESOURCE_GROUP
az containerapp list --resource-group $group --query "[].{name:name,revision:properties.latestRevisionName}" --output table
```

Select one app and check its registry association:

```powershell
$app = "<actual-container-app-name>"
$registry = azd env get-value AZURE_CONTAINER_REGISTRY_RESOURCE_ID
$principal = az containerapp show --resource-group $group --name $app --query identity.principalId --output tsv
az containerapp show --resource-group $group --name $app --query "properties.configuration.registries" --output json
az role assignment list --assignee $principal --scope $registry --include-inherited --query "[].{role:roleDefinitionName,scope:scope}" --output table
```

Repeat for UI, gateway, inventory, orders, and dashboard. Missing scoped access is a deployment blocker; repair it through reviewed infrastructure/permission changes, not a broad subscription role or credential fallback. A registry using a different permission mode, such as repository ABAC, needs a reviewed adaptation rather than blindly reusing this sample's `AcrPull` assumptions.

## Publish images and apply application ports

`azd publish` builds and pushes an image without switching the app away from its placeholder configuration. Publish all five supporting services first so that the next infrastructure pass can apply each image together with the correct port and readiness/liveness probes.

Do not use plain `azd deploy <supporting-service>` for this initial switch: it preserves placeholder port 80. The second `azd provision infra` is required to apply the matching infrastructure settings. It is not a transaction that guarantees all five apps become healthy at once.

```powershell
azd publish status-dashboard
azd publish inventory-mcp
azd publish work-orders-api
azd publish gateway
azd publish ui
```

Verify every output is nonempty with `azd env get-value <setting>` before continuing:

| Service | Required image setting | Application target port | Ingress |
|---|---|---|---|
| Status dashboard | `SERVICE_STATUS_DASHBOARD_IMAGE_NAME` | 8003 | Internal |
| Inventory MCP | `SERVICE_INVENTORY_MCP_IMAGE_NAME` | 8001 | External, API key |
| Work orders | `SERVICE_WORK_ORDERS_API_IMAGE_NAME` | 8002 | External, API key |
| Gateway | `SERVICE_GATEWAY_IMAGE_NAME` | 8000 | Internal |
| UI | `SERVICE_UI_IMAGE_NAME` | 80 | External, Entra and allowlist |

```powershell
azd provision infra
```

Preserve all five image settings: an empty value selects the placeholder again. Verify revision health, target port, image reference, and probes for each app. The cloud gateway listens on 8000; local development uses 8080.

```powershell
az containerapp show --resource-group $group --name $app --query "{state:properties.provisioningState,ingress:properties.configuration.ingress,containers:properties.template.containers[].{name:name,image:image,probes:probes}}" --output json
az containerapp revision list --resource-group $group --name $app --query "[].{name:name,active:properties.active,health:properties.healthState}" --output table
```

The UI requires `GATEWAY_HOST=<internal-gateway-host>` and `GATEWAY_URL=https://<internal-gateway-host>/api/`. Its Nginx proxy validates upstream TLS and SNI and allows 600-second streams. Keep `proxy_ssl_verify_depth 3`; do not disable certificate verification to hide a 502.

The gateway requires `AGENT_MODE=hosted`, `HOSTED_AGENT_ENDPOINT=<project-endpoint>`, `HOSTED_AGENT_NAME=fibey-agent`, and the intended tenant. Exact comma-separated `CORS_ORIGINS` are supported; the same-origin UI proxy does not require wildcard CORS.

## Ingest knowledge and register the toolbox

The document pipeline is separate from container deployment. The knowledge script uploads the eight bundled Markdown files to the private `foundry-iq-docs` blob container, configures a Search data source/index/indexer, waits for a new successful indexing run, and creates the knowledge source/base and Foundry connection.

The toolbox script then reads the deployed work-orders OpenAPI specification and registers inventory MCP, four work-order operations, and knowledge retrieval. It stores API credentials in Foundry connections, not in the toolbox JSON. No browser service, reset/admin tool, or additional agent is created.

Optionally run configuration-only checks after the required outputs and secrets exist:

```powershell
pwsh -File .\scripts\setup-knowledge-base.ps1 -EnvironmentName "<environment-name>" -CheckOnly
pwsh -File .\scripts\setup-toolbox.ps1 -EnvironmentName "<environment-name>" -CheckOnly
```

`-CheckOnly` checks local settings and tooling; it does not test cloud authorization or reachability. When ready, run the real setup in order:

```powershell
pwsh -File .\scripts\setup-knowledge-base.ps1 -EnvironmentName "<environment-name>"
pwsh -File .\scripts\setup-toolbox.ps1 -EnvironmentName "<environment-name>"
```

| Contract | Configured behavior |
|---|---|
| Search data source/index/indexer/knowledge source | Search `2026-04-01` object APIs |
| Knowledge base and MCP retrieval | `2026-08-01-preview`; minimal reasoning, extractive output |
| Retrieval defaults | At most three output documents and 6,000 output tokens by default; no extra model required by this minimal pipeline |
| Knowledge connection | `kb-fibey-field-ops-kb`; project managed identity; Search audience |
| Inventory connection | `fibey-inventory-mcp`; remote MCP and `x-api-key` |
| Work-orders connection | `fibey-work-orders-api`; OpenAPI `project_connection`; credential named `x-api-key`, not `APIKeyHeader` |
| Toolbox | `fibey-toolbox`; published version; consumer MCP endpoint with `api-version=v1` |

Use the scripts instead of manually copying outdated Search payloads. Knowledge reruns overwrite matching blobs and reindex; deleting a local document does not delete the existing blob. Toolbox reruns upsert connections and publish a version, potentially changing all consumers of the default endpoint.

The toolbox explicitly allows unattended MCP calls; the UI cannot collect and resume a pending approval. Setting `require_approval` in configuration or writing "ask first" in a prompt is not an enforced operational-write control.

## Deploy the hosted agent and accept the solution

Deploy the agent only after its model, toolbox, downstream services, and access checks are ready. The agent image enters the Foundry-managed runtime; it is not added to the five-app ACA environment.

Keep the existing supported SDK integration and dependency locks. The image entrypoint remains `python -m fibey.agent.hosted`, using `FoundryToolbox` and `ResponsesHostServer.run_async()`; do not recreate the removed standalone `agent.yaml`.

```powershell
azd deploy fibey-agent
```

Open your environment's `WEB_URL` and sign in as the allowlisted user. Record the actual hosted-agent version, toolbox version, model deployment, and supporting image/revision identifiers with redacted acceptance evidence.

| Acceptance check | Pass evidence |
|---|---|
| UI authentication | Anonymous request redirects to Entra; non-allowlisted user is denied; allowlisted user can use chat |
| Internal services | Gateway and dashboard ingress are internal and not usable as public application entrypoints |
| Operational API protection | Inventory and orders reject absent/incorrect keys; health endpoints may be anonymous for probes |
| Tool discovery and execution | Eleven operational tools available; inventory and WO-007 lookups complete with real activity |
| Knowledge | New indexer run succeeds, expected documents are indexed, procedure answer includes source references |
| Status | Inventory `get_network_status` reads the configured internal dashboard |
| Combined task | WO-007 briefing uses work-order, stock, knowledge, and status results without invented gaps |
| Continuity/reset | Follow-up uses prior context; reset starts new chat context without resetting work orders |
| Synthetic write | Read current state, perform one change, read it back; no approval enforcement claimed |
| Streaming | Successful response terminates once; failed/truncated response reports an error |
| Observability | ACA logs available; synthetic hosted trace received by the intended project-linked sink |

Do not treat provisioning, `/health`, tool enumeration, or a `[DONE]` frame after an error as end-to-end success. See the [session walkthrough](docs/session-overview.md) for the presentation prompts and expected teaching evidence.

## Diagnose failures by boundary

Start with the first failed boundary and the identity used there. Changing SDK internals, turning off TLS, or granting broad access can hide the symptom while leaving the deployment incorrect.

Use synthetic requests, timestamps, session/request identifiers, and redacted logs. Hosted OpenTelemetry is enabled with sensitive content disabled by default. The Bicep creates ACA Log Analytics, not Application Insights: verify the Foundry project's linked sink and exporter rather than assuming traces are stored.

| Symptom | Inspect first |
|---|---|
| Provisioning denied | Target subscription/region, resource permissions, role-assignment permission, quota |
| Image pull or revision startup fails | Image exists; all five identities have pull roles; registry association uses `system`; correct application port/probes |
| Entra login loops or denies the intended user | Tenant, client ID/secret expiry, callback URI, allowed user object ID |
| UI 502 or failed startup | Exact Nginx upstream values, internal gateway revision, TLS trust/SNI/chain depth |
| Hosted 401/403 | Gateway role on project, `https://ai.azure.com/.default` audience, runtime identity and project access |
| Tool discovery fails | Published/default toolbox version and all source endpoints/connections; one failed source can block startup |
| Inventory/orders 401 | Deployed API key matches the corresponding connection credential |
| OpenAPI authentication error | `project_connection` and `x-api-key` header name, not the schema identifier |
| Blob upload or indexing fails | Operator Blob data role; Search identity Blob reader role; new indexer run and document count |
| Knowledge 403 or schema error | Project identity Search data role, MCP API version, actual `query_variants` input schema |
| Knowledge unexpectedly requests a model | Explicit minimal reasoning and extractive output in knowledge-base defaults |
| 429 during a briefing | Model TPM/RPM allocation, concurrent requests, batched stock checks, retrieval budgets |
| Lost follow-up context | Gateway restart, response mapping, compute-session affinity; gateway must remain one replica |
| Truncated/hanging stream | Response terminal event, timeout, proxy buffering, malformed SSE; do not discard errors |

Inspect recent logs for a selected supporting app, without enabling debug or dumping credentials:

```powershell
az containerapp logs show --resource-group $group --name $app --type system --tail 50
az containerapp logs show --resource-group $group --name $app --type console --tail 50
```

System logs help diagnose platform/revision issues; console logs help diagnose application startup and requests. Restrict access to both. See [toolbox integration](docs/toolbox-integration.md) for runtime call-ID, skills, and streaming details.

## DevOps, GitOps, and release management

DevOps connects development changes with repeatable deployment and operation. GitOps treats reviewed, versioned desired state as the input to controlled reconciliation. Fibey includes source, Bicep, setup scripts, and locks that support those practices; it does **not** include a configured CI/CD pipeline, automated approval gate, or GitOps controller.

Use the following as a release design when adapting the sample. Keep application release approvals distinct from approval of an individual work-order write: a deployment gate cannot authorize later operational actions.

| Stage | Suggested release gate |
|---|---|
| Review | Review `azure.yaml`, Bicep, prompts, skills, OpenAPI changes, credentials/identity boundaries, and dependency locks together |
| Validate | Run existing Python tests and UI build; check infrastructure changes and tool schema compatibility |
| Build | Produce traceable container artifacts; record immutable digests plus the source commit and model configuration |
| Authenticate | Use a scoped federated CI identity; obtain secrets from approved storage, not checked-in environment files |
| Provision/promote | Apply the staged rollout; promote tested toolbox and hosted-agent versions, preserving all supporting image settings |
| Accept | Run protected-path, tool, citation, state, stream, and telemetry checks in the target environment |
| Observe | Set latency/error/token budgets and monitor authorization failures, 429s, downstream failures, and revision health |
| Reconcile | Review drift and reconcile intended settings; never silently overwrite an operator change in a shared environment |

The toolbox's unversioned consumer endpoint follows its published default version under the current platform contract. Use a version-specific developer endpoint for candidate testing, record the accepted default, and recheck consumers after promotion. Updating a connection can affect consumers even without rebuilding their images.

For rollback, retain the previous supporting image references and configuration, the accepted toolbox version, and the previous hosted-agent version. Reapply compatible supporting settings, promote the known-good toolbox version, and use the supported Foundry version-switch procedure. Re-run acceptance checks; reverting a Git commit alone does not undo remote configuration or data writes. No automated rollback is supplied here.

Run the existing local checks with frozen dependencies:

```powershell
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -p "test_*.py"
Set-Location ui
npm ci
npm run build
```

## Operate, reset, and retire the demo safely

The gateway and synthetic order service use one replica because their state is in memory. Scale the application only after externalizing state, enforcing session ownership, and testing concurrency, retries, quotas, and recovery. The hosted platform's scaling capabilities do not solve those application-level constraints.

Reset chat clears conversation mappings but neither resets work orders nor deletes old remote compute sessions. Restarting the work-orders service reloads all seed data and discards every in-memory change. Plan resets with other demonstrators rather than exposing a reset operation as an agent tool.

Track Entra client-secret expiry and rotate it in both Entra and the selected azd/ACA configuration. Rotate inventory/orders keys together with their matching Foundry connections and verify rejection of old credentials. Do not enable `ENABLE_SENSITIVE_TELEMETRY=true` except for an explicitly controlled synthetic-data investigation.

For teardown, first inventory the exact environment's resources, shared ACR/Foundry dependencies, Entra registration, retained images, and log/data retention requirements. Obtain approval for the specific resources to remove. Removing ACA apps alone does not remove model, Search, storage, registry, or telemetry costs; removing a shared resource group can disrupt other samples. This guide deliberately provides no blind resource-group deletion command.

Before real operations, add durable transactional storage, idempotency, enforced approvals, audit records, per-user authorization, appropriate private networking/egress controls, secret management, evaluation, SLOs, and disaster-recovery procedures. [Multi-agent coordination](docs/session-overview.md#multi-agent-coordination-extension-not-deployed) remains an extension design, not deployed behavior.

## Platform references

Use the repository's pinned configuration for this sample and current Microsoft documentation for platform support, permissions, and API lifecycle. Preview knowledge-base APIs and extension command surfaces can evolve independently of the repository.

These references explain the boundaries most likely to matter when adapting or operating Fibey.

| Reference | Topic |
|---|---|
| [Hosted agents](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents) | Runtime, identity, protocols, versions, and observability |
| [Deploy a hosted agent](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent) | Supported hosted deployment workflow |
| [Hosted agent toolbox integration](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/use-toolbox-hosted-agent) | Consumer/developer endpoints and approval responsibility |
| [Create a Search knowledge base](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base) | Retrieval configuration and API versions |
| [Azure built-in roles](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles) | Verify role definitions and scopes |
