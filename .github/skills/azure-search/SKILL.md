---
name: "Azure Search Ops"
description: "Operate the Azure AI Search index and knowledge base behind FoundryIQ for Fibey field ops."
tags: ['azure', 'ai-search', 'knowledge-base', 'foundryiq', 'rag', 'ops']
---

# Azure Search Ops Skill

You are a specialist for **operating the Azure AI Search index and the
Knowledge Base (KB)** that the Fibey agent uses via Foundry Toolbox /
FoundryIQ. You don't manage the agent or its prompts — that's the Agent
Developer skill. You focus on **content freshness, schema correctness, and
retrieval quality**.

## Mental model

```text
services/foundry-iq-docs/docs/*.md
        │
        ▼  Blob container "foundry-iq-docs"
        │
        ▼  AI Search indexer "foundry-iq-docs-indexer"
        │
        ▼  AI Search index   "foundry-iq-docs-index"
        │       └─ semantic config "default"
        │
        ▼  Knowledge Source  "fibey-field-ops-ks"  (kind=searchIndex)
        │
        ▼  Knowledge Base    "fibey-field-ops-kb"
        │
        ▼  Foundry connection "fibey-search"  (CognitiveSearch + ApiKey)
        │
        ▼  Foundry Toolbox  →  agent retrieves via azure_ai_search tool
```

## Key facts

- **Search service API version (index/indexer ops):** `2024-07-01`.
- **Knowledge Base API version:** `2026-04-01` (GA). The KB/KS endpoints use
  **OData function syntax**: `knowledgebases('<name>')`,
  `knowledgebases('<name>')/retrieve`. Path-style `/knowledgebases/<name>`
  returns HTTP 405.
- **Knowledge Source body:** `{ kind: "searchIndex", searchIndexParameters: { searchIndexName, sourceDataFields, ... } }`.
- **KB retrieve body:** `{ intents: [ { search: "<query>", type: "semantic" } ], knowledgeSourceParams: [ ... ] }`.
- **Foundry connection that works:** `CognitiveSearch` + `ApiKey` + Foundry
  tool type `azure_ai_search`. `RemoteTool` + `ProjectManagedIdentity` ->
  KB MCP endpoint returns HTTP 403.
- **Indexer status `reset` is NOT terminal** — it represents the prior reset
  request, not the in-flight run. Poll past it.
- Bootstrap is done by `scripts/setup-knowledge-base.sh` (kept). Day-to-day
  ops are the inline `az`/`curl` commands below.

## Required env

| Var | Used for |
|---|---|
| `AZURE_RESOURCE_GROUP` | Resolves search service / storage |
| `AZURE_SEARCH_ENDPOINT` | Override; otherwise `https://<svc>.search.windows.net` |
| `AZURE_SEARCH_ADMIN_KEY` | Override; otherwise fetched via `az search admin-key show` |
| `STORAGE_ACCOUNT` | Override; otherwise from azd outputs |

Get an admin key:

```bash
SVC=fibey-apps-search   # or your env's search service
RG=rg-fibey-westus2
KEY=$(az search admin-key show --service-name "$SVC" --resource-group "$RG" --query primaryKey -o tsv)
```

## Inline operations

These replace the previous wrapper scripts. Run from repo root with `.env`
exported (`set -a && . .env && set +a`).

### Inspect index health

```bash
SVC=fibey-apps-search
INDEX=foundry-iq-docs-index
INDEXER=foundry-iq-docs-indexer
EP="https://$SVC.search.windows.net"
KEY=$(az search admin-key show --service-name "$SVC" -g "$AZURE_RESOURCE_GROUP" --query primaryKey -o tsv)

# Doc count
curl -fsS -H "api-key: $KEY" \
  "$EP/indexes/$INDEX/docs/\$count?api-version=2024-07-01"

# Latest indexer run
curl -fsS -H "api-key: $KEY" \
  "$EP/indexers/$INDEXER/status?api-version=2024-07-01" \
  | jq '.lastResult | {status, itemsProcessed, itemsFailed, errors, startTime, endTime}'

# Schema
curl -fsS -H "api-key: $KEY" \
  "$EP/indexes/$INDEX?api-version=2024-07-01" \
  | jq '{fields: [.fields[] | {name, type, key, retrievable, searchable}], semantic, vectorSearch}'

# Plain search (sanity check)
curl -fsS -H "api-key: $KEY" \
  "$EP/indexes/$INDEX/docs?api-version=2024-07-01&search=*&\$top=3" | jq
```

### Reindex (after editing docs in services/foundry-iq-docs/docs/)

```bash
ACCT=<your storage account>
CONT=foundry-iq-docs
KEY=$(az storage account keys list -g "$AZURE_RESOURCE_GROUP" -n "$ACCT" --query "[0].value" -o tsv)

# Upload (overwrites)
az storage blob upload-batch --account-name "$ACCT" --account-key "$KEY" \
  --destination "$CONT" --source services/foundry-iq-docs/docs --pattern "*.md" --overwrite

# Run the indexer
SVC_KEY=$(az search admin-key show --service-name "$SVC" -g "$AZURE_RESOURCE_GROUP" --query primaryKey -o tsv)
curl -fsS -X POST -H "api-key: $SVC_KEY" \
  "$EP/indexers/$INDEXER/run?api-version=2024-07-01"

# Poll until terminal (success / transientFailure / persistentFailure).
# IMPORTANT: ignore status "reset" (not terminal) and empty bodies.
for i in {1..60}; do
  STATUS=$(curl -fsS -H "api-key: $SVC_KEY" \
    "$EP/indexers/$INDEXER/status?api-version=2024-07-01" \
    | jq -r '.lastResult.status // "running"')
  echo "[$i] $STATUS"
  case "$STATUS" in
    success|transientFailure|persistentFailure) break ;;
  esac
  sleep 5
done
```

For a full rebuild, call `POST .../indexers/$INDEXER/reset` first, then run
the indexer. Don't bail on the first `reset` status while polling.

### Test the Knowledge Base directly

```bash
# KB config
curl -fsS -H "api-key: $SVC_KEY" \
  "$EP/knowledgebases('fibey-field-ops-kb')?api-version=2026-04-01" | jq

# Retrieve
curl -fsS -X POST -H "api-key: $SVC_KEY" -H "Content-Type: application/json" \
  "$EP/knowledgebases('fibey-field-ops-kb')/retrieve?api-version=2026-04-01" \
  -d '{
    "intents": [{ "search": "how do I splice single-mode fiber", "type": "semantic" }],
    "knowledgeSourceParams": [{
      "kind": "searchIndex",
      "knowledgeSourceName": "fibey-field-ops-ks"
    }]
  }' | jq
```

## Standard playbooks

### "I edited markdown in services/foundry-iq-docs/docs/"
1. Upload + run indexer (snippet above).
2. Verify `lastResult.status == success` and doc count matches expectations.
3. Run a KB retrieve for a question your new content should answer.

### "Agent says 'no results' for things it should know"
1. Doc count > 0? Indexer `success`? Schema as expected?
2. Run a direct KB retrieve. If it returns content, the issue is upstream
   (Foundry Toolbox connection, agent prompt, or the agent's filtering).
   Switch to the **Foundry Toolbox Ops** skill.
3. If the KB retrieve is also empty but the index has docs, check the
   semantic config + the index field names against the KS `sourceDataFields`.

### "I need to change the index schema"
1. GET the existing index, edit fields/semantic/vector config.
2. PUT it back (`api-version=2024-07-01`). Some changes require recreating
   the index — non-breaking field additions are OK in place.
3. Reset + rerun the indexer to fully rebuild.
4. Update `scripts/setup-knowledge-base.sh` so future bootstraps match.
5. If `sourceDataFields` or semantic config changed, also update the KS body
   inside `setup-knowledge-base.sh` (and PUT to the KS endpoint).

### Symptoms that indicate index corruption
- `lastResult.status == persistentFailure` repeatedly with the same error.
- Doc count is 0 but blobs exist and indexer reports success — schema/KS mismatch.
- KB retrieve always returns 0 hits for queries that match `search=*` results.

Recovery: `POST /indexers/$INDEXER/reset`, then re-run. If that doesn't
help, DELETE + recreate the index and re-run `setup-knowledge-base.sh`.

## Don'ts

- Don't recreate the KB just to refresh docs — reindex instead.
- Don't hardcode admin keys; fetch on demand with `az search admin-key show`.
- Don't use path-style KB URLs (`/knowledgebases/<name>`) — they return 405.
  Use OData function syntax: `knowledgebases('<name>')`.
- Don't treat indexer status `reset` as terminal in your polling loop.
- Don't add env vars to operational commands without also adding them to `.env.example`.
