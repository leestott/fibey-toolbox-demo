# Hosted-agent infrastructure notes

This directory is a documentation reference, not an independently deployable infrastructure root. Run deployment commands from the demo root using `azure.yaml`, which defines the Foundry project host, hosted agent, model deployment, and five supporting ACA services.

The reference deployment runs in `leestott-mcpchennai`, North Central US. Hosted agent version 1 and toolbox version 5 completed a grounded multi-tool briefing; all five supporting apps are deployed. Follow the [deployment guide](../docs/deployment.md) for the current state, access requirements, and repeatable deployment checks.

## Sources of truth

The project and agent are represented together so configuration does not drift between competing manifests. The obsolete standalone `agent.yaml` was unused by the current azd configuration and has been removed.

The hosted agent is not an ACA service. Its container still needs to be built, pushed, started, and verified, but Foundry owns the agent runtime and Responses protocol endpoint.

| File | Responsibility |
|---|---|
| `azure.yaml` | Project/model and hosted agent; Responses `2.0.0`; five ACA services |
| `infra/foundry/` | Foundry provisioning layer |
| `infra/main.bicep`, `infra/apps.bicep` | Supporting protected ACA and knowledge infrastructure |
| `Dockerfile.agent` | Locked Python runtime and non-root hosted entrypoint |
| `pyproject.toml`, `uv.lock` | Authoritative Python dependency specification and resolution |
| `requirements.txt` | Pinned export for supporting image installation |
| `src/fibey/agent/hosted.py` | `FoundryToolbox`, skills, telemetry, and `ResponsesHostServer` |

## Follow the staged deployment

Provision Foundry first, then configure model/toolbox aliases and the protected UI/API prerequisites. The ACA launch has two phases: run `azd provision infra` for placeholder apps, then verify all five apps' `AcrPull` roles and the operator's image-build/push permissions. Run `azd publish <service>` for status-dashboard, inventory-mcp, work-orders-api, gateway, and ui before applying any real-image configuration.

ACA also requires an explicit registry-identity association: the shared container-app module sets `configuration.registries` to the supplied registry server with `identity: 'system'`. `azd deploy` does not add that link automatically. Once all five `SERVICE_*_IMAGE_NAME` settings exist, run `azd provision infra` again to apply their images, actual ports, and probes together. Plain `azd deploy` preserves placeholder port 80, so it cannot perform the initial switch to the APIs' ports 8000–8003.

Verify the supporting revisions before running the knowledge and toolbox setup scripts. Only then deploy the hosted agent with `azd deploy fibey-agent`. See the [full deployment sequence](../docs/deployment.md) rather than using a separate template or a blanket deployment command.

The model is **GPT-5.4-mini**, with deployment name `gpt-5.4-mini`. Runtime configuration is supplied through `azure.yaml` and the selected azd environment, not hardcoded account URLs:

| Runtime setting | Source |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Foundry hosting context; explicit configuration for local execution |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | `azure.yaml` hosted service environment |
| `TOOLBOX_NAME` | `azure.yaml` hosted service environment |
| `TOOLBOX_ENDPOINT` | Optional exact toolbox URL override where explicitly configured |
| Azure identity context | Foundry hosting; Azure credentials and scoped role assignments still apply |
| `ENABLE_SENSITIVE_TELEMETRY` | Optional explicit content-tracing opt-in; default off |

## Keep the demo boundaries visible

The UI is Entra-only and allowlisted; gateway and status are internal. Inventory and work orders are externally reachable but key-protected, and status is fetched by a narrow inventory tool rather than browser automation.

One gateway replica preserves in-memory conversation mapping. One work-orders replica holds resettable synthetic data; a restart resets it, whereas chat reset only clears history. There is no enforced approval UI or production durability guarantee.

For the request flow, skills fallback, credential lifecycle, and streaming rules, read [Toolbox integration](../docs/toolbox-integration.md).
