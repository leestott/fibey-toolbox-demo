# Fibey deployment guide

The maintained deployment procedure is now [deployment_guide.md at the repository root](../deployment_guide.md). It covers prerequisites, Azure resources, RBAC, protected-service setup, staged deployment, acceptance checks, troubleshooting, and release/rollback practices.

Run its commands from the repository root. `azure.yaml` remains authoritative: one Foundry-hosted agent using GPT-5.4-mini and Responses `2.0.0`, plus five supporting Azure Container Apps. This page preserves existing links without maintaining a competing procedure.

The required initial order is Foundry provisioning, prerequisite configuration, placeholder infrastructure, publication of all five supporting images, a second infrastructure pass, knowledge/toolbox setup, and hosted-agent deployment. **Do not substitute plain `azd deploy` for the initial supporting-image switch**: it preserves placeholder port 80 instead of applying the real application ports and probes.

Use [the engineering architecture](architecture.md) to understand the boundaries and [the session walkthrough](session-overview.md) to verify the demonstration. Successful provisioning is not proof that protected sign-in, authorization, tool calls, or chat streaming work end to end.
