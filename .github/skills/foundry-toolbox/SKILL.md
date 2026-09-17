---
name: "Foundry Toolbox Ops"
description: "Operate the Foundry Toolbox and Foundry-hosted agents for the Fibey project: inspect, version, recreate, and smoke-test."
tags: ['azure', 'foundry', 'toolbox', 'mcp', 'hosted-agents', 'ops']
---

# Foundry Toolbox Ops Skill

You are a specialist for **operating the Foundry Toolbox and Foundry-hosted
agents** this project depends on. You don't write new agent code — that's
the Agent Developer skill. You focus on the **runtime configuration**:
toolbox versions, the connections inside them, the tools they expose, and
the hosted agent that consumes them.

## Mental model

```text
Foundry account (e.g. ai-fibey)
  └─ Project (e.g. fibey-project-westus2)
       ├─ Connections/        (CognitiveSearch, OpenAPI, MCP, ...)
       │     └─ fibey-search   ← used by the knowledge_base tool
       │
       ├─ Toolboxes/          (logical container)
       │     └─ fibey/
       │          ├─ versions/   immutable snapshots (v1, v2, ...)
       │          └─ default_version: "1"
       │
       └─ Agents/
             └─ fibey-agent     references a toolbox via MCP URL
```

The agent connects via a **versioned MCP URL**:

```text
{FOUNDRY_PROJECT_ENDPOINT}/toolboxes/{name}/versions/{n}/mcp?api-version=v1
```

> **Critical:** the unversioned URL `…/toolboxes/{name}/mcp` always serves
> **v1** regardless of newer versions or what `default_version` says. Prefer
> the versioned URL when pinning the agent to a specific version. The agent
> auto-appends `?api-version=v1` if missing (see `src/fibey/agent/agent.py`).

## Key facts

- **Foundry data-plane API version:** `v1`.
- **AAD scope for data-plane:** `https://ai.azure.com/.default`
  (NOT `cognitiveservices.azure.com` — that returns 401).
- **Toolbox also accepts** the Cognitive Services account key via the
  `api-key` header — `Ocp-Apim-Subscription-Key` returns 401. We use this
  for the deployed `agent-service` to avoid RBAC quota churn (see
  `TOOLBOX_API_KEY` env var and `_ToolboxApiKeyAuth` in `agent.py`).
- **Toolbox creation:** `POST /toolboxes/{name}/versions`. `POST /toolboxes`
  and `PUT /toolboxes/{name}` both return HTTP 405.
- **Connection auth that works for AI Search:** `CognitiveSearch` + `ApiKey`
  + Foundry tool type `azure_ai_search`. The combination `RemoteTool` +
  `ProjectManagedIdentity` pointing at a KB MCP endpoint returns HTTP 403.
- **Subscription `921496dc-...`** has historically been near its
  4000-role-assignment cap. Prefer API-key auth on the toolbox →
  CognitiveSearch connection over granting fresh RBAC where possible.

## Required env

Read from `.env` (root) or `.azure/<env>/.env` (azd):

| Var | Used for |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Data-plane base, e.g. `https://ai-fibey.services.ai.azure.com/api/projects/fibey-project-westus2` |
| `TOOLBOX_MCP_URL`          | What the agent connects to (versioned MCP URL) |
| `TOOLBOX_API_KEY`          | Optional: Cognitive Services account key for api-key auth to the toolbox |
| `HOSTED_AGENT_NAME`        | Hosted agent name (hosted mode only) |
| `HOSTED_AGENT_ENDPOINT`    | Hosted agent endpoint (gateway hosted mode) |

Get a token to use in `curl` calls:

```bash
TOK=$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)
```

## Inline operations

These replace previous wrapper scripts. Run them from the repo root with
`.env` already exported (`set -a && . .env && set +a`).

### List toolboxes and inspect a version

```bash
TOK=$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)
BASE="$FOUNDRY_PROJECT_ENDPOINT"

# List toolboxes
curl -fsS "$BASE/toolboxes?api-version=v1" -H "Authorization: Bearer $TOK" | jq

# Versions of one toolbox
curl -fsS "$BASE/toolboxes/fibey/versions?api-version=v1" \
  -H "Authorization: Bearer $TOK" | jq '.data[] | {version, tools: [.tools[].type]}'

# Full definition of one version
curl -fsS "$BASE/toolboxes/fibey/versions/1?api-version=v1" \
  -H "Authorization: Bearer $TOK" | jq
```

### Smoke-test the toolbox MCP endpoint

```bash
URL="$TOOLBOX_MCP_URL"
TOK=$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)

curl -fsS -X POST "$URL" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}'
```

Or with the **account key** (matches deployed agent-service):

```bash
KEY=$(az cognitiveservices account keys list -g <rg> -n <account> --query key1 -o tsv)
curl -fsS -X POST "$URL" -H "api-key: $KEY" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Recreate a toolbox in a different project

Use when a referenced connection is deleted or the project workspace is at
its 120-connection cap. Clone the source definition, prune fields the API
rejects on create, and POST to the new project.

```bash
# 1. Dump source definition
TOK_OLD=$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)
curl -fsS "$SOURCE_ENDPOINT/toolboxes/fibey/versions/9?api-version=v1" \
  -H "Authorization: Bearer $TOK_OLD" > /tmp/source.json

# 2. Prepare clean payload in Python (strip id/created_at/version fields,
#    point connections at IDs in the new project). Don't redirect stdout
#    from a Python heredoc — print() pollutes the file. Write inside Python:
#    with open('/tmp/body.json','w') as f: json.dump(body, f)

# 3. Create in target project
TOK_NEW=$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)
curl -fsS -X POST "$NEW_ENDPOINT/toolboxes/fibey/versions?api-version=v1" \
  -H "Authorization: Bearer $TOK_NEW" \
  -H "Content-Type: application/json" \
  -d @/tmp/body.json | jq
```

### Hosted agent inspection

```bash
TOK=$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)
BASE="$FOUNDRY_PROJECT_ENDPOINT"

# List agents
curl -fsS "$BASE/agents?api-version=2025-11-15-preview" -H "Authorization: Bearer $TOK" | jq

# Show one agent
curl -fsS "$BASE/agents/$HOSTED_AGENT_NAME?api-version=2025-11-15-preview" \
  -H "Authorization: Bearer $TOK" | jq
```

### Update deployed services after a toolbox/version change

The gateway runs in `containerapp` mode and proxies to `agent-service`. The
actually-relevant env vars live on `fibey-apps-agent-service`:

```bash
NEW_EP="https://ai-fibey.services.ai.azure.com/api/projects/fibey-project-westus2"
NEW_TB="${NEW_EP}/toolboxes/fibey/mcp?api-version=v1"
KEY=$(az cognitiveservices account keys list -g rg-fibey-westus2 -n ai-fibey --query key1 -o tsv)

az containerapp secret set -n fibey-apps-agent-service -g rg-fibey-westus2 \
  --secrets toolbox-api-key="$KEY"

az containerapp update -n fibey-apps-agent-service -g rg-fibey-westus2 \
  --set-env-vars "FOUNDRY_PROJECT_ENDPOINT=$NEW_EP" \
                 "TOOLBOX_MCP_URL=$NEW_TB" \
                 "TOOLBOX_API_KEY=secretref:toolbox-api-key"
```

> `azd deploy <service>` rebuilds the image but does **not** push env-var
> changes for azd-managed container apps. Update env vars via `az containerapp
> update` (or `azd env set` + full `azd up`/redeploy through bicep wiring).

## Standard playbooks

### Adopt a new toolbox version
1. List versions and confirm the new one exposes the expected tools.
2. Update `TOOLBOX_MCP_URL` in `.env` (and `.azure/<env>/.env` for deployed).
3. For containerapp deployment, run the `az containerapp update` block above.
4. Restart the gateway / agent-service container revision.
5. Smoke-test via the agent CLI or a `/api/chat` request.

### Diagnose "tool not found" / ARA 403 errors
- Check `TOOLBOX_MCP_URL` includes `/versions/<N>/` — the unversioned URL is pinned at v1.
- Use the inspect commands above to verify the expected connection exists in that version.
- For Azure Search KB calls, confirm the connection is `CognitiveSearch + ApiKey + azure_ai_search`.
- If running deployed: confirm the agent-service MSI has Cognitive Services User / OpenAI User / Azure AI User on the **account** (these inherit to projects).

### Recreate the toolbox in a fresh project (cap or corruption)
1. Confirm the new account / project exists (`az cognitiveservices account show`, etc.).
2. Verify model deployments are present.
3. If using AAD: grant the agent-service MSI Cognitive Services User / Cognitive Services OpenAI User / Azure AI User (renamed from "Azure AI Developer") on the new account.
4. Create connections in the new project (e.g. `fibey-search` → CognitiveSearch + ApiKey).
5. POST the cleaned toolbox payload (see "Recreate" snippet above).
6. Update `.env` + `.azure/<env>/.env` + agent-service container app env vars.

## Don'ts

- Don't commit `.env`, `.azure/<env>/.env`, or `agent.yaml.bak`.
- Don't add a `latest` alias for toolbox versions — always be explicit.
- Don't redirect a Python heredoc's stdout to a JSON file; `print()` pollutes the file. Open the file inside the script.
- Don't use the Cognitive Services scope (`https://cognitiveservices.azure.com/.default`) for data-plane calls — it 401s.
- Don't grant new RBAC on subscription `921496dc-987f-410f-bd57-426eb2611356` without first freeing existing slots; it hovers near the 4000 cap.
