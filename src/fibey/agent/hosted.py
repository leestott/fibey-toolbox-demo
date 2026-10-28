"""Fibey's Foundry-hosted Responses entrypoint.

Requires FOUNDRY_PROJECT_ENDPOINT and either TOOLBOX_ENDPOINT or TOOLBOX_NAME.
Hosted instructions and model come from .agent_configs/. SKILLS_SOURCE defaults
to auto (published skills with bundled fallback); file skips discovery, mcp
requires published skills.
Set ENABLE_SENSITIVE_TELEMETRY=true only to explicitly opt into content tracing.
"""

import asyncio
import logging
import os
from contextlib import AsyncExitStack
from pathlib import Path

from agent_framework import (
    Agent,
    CachingSkillsSource,
    FileSkillsSource,
    MCPSkillsSource,
    Skill,
    SkillsProvider,
    SkillsSource,
    SkillsSourceContext,
)
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import configure_otel_providers
from agent_framework_foundry_hosting import FoundryToolbox, ResponsesHostServer
from azure.ai.agentserver.optimization import OptimizationConfig, load_config
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential as SyncDefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SKILLS_PATH = Path(__file__).parent / "skills"
AGENT_CONFIGS_PATH = Path(__file__).resolve().parents[3] / ".agent_configs"


class FibeySkillsSource(SkillsSource):
    """Discover published skills on the authenticated toolbox session, preserving defaults."""

    def __init__(self, toolbox: FoundryToolbox, mode: str = "auto"):
        if mode not in {"auto", "file", "mcp"}:
            raise ValueError("SKILLS_SOURCE must be auto, file, or mcp")
        self.mode = mode
        self.toolbox = toolbox
        self.bundled = FileSkillsSource(SKILLS_PATH)
        self.published = MCPSkillsSource(session_provider=self._session)

    def _session(self):
        if self.toolbox.session is None:
            raise RuntimeError("The toolbox must be connected before skills discovery")
        return self.toolbox.session

    async def get_skills(self, context: SkillsSourceContext) -> list[Skill]:
        bundled = await self.bundled.get_skills(context)
        if not bundled:
            raise RuntimeError("Bundled Fibey skills are missing")
        if self.mode == "file":
            return bundled
        try:
            async with asyncio.timeout(30):
                published = await self.published.get_skills(context)
        except Exception as exc:
            if self.mode == "mcp":
                raise
            logger.warning("Published skills unavailable (%s); using bundled skills", type(exc).__name__)
            return bundled
        if not published:
            if self.mode == "mcp":
                raise RuntimeError("SKILLS_SOURCE=mcp requires published toolbox skills")
            logger.info("No published skills; using %d bundled skills", len(bundled))
            return bundled
        # Published versions override matching bundled skills, not the entire skill set.
        merged = {skill.frontmatter.name: skill for skill in bundled}
        merged.update({skill.frontmatter.name: skill for skill in published})
        logger.info("Loaded %d skills (%d published)", len(merged), len(published))
        return list(merged.values())


def _load_optimization_config() -> OptimizationConfig:
    # azd applies candidates at the service root, not beside this module entrypoint.
    config_dir = os.getenv("OPTIMIZATION_LOCAL_DIR") or str(AGENT_CONFIGS_PATH)
    with SyncDefaultAzureCredential() as credential:
        config = load_config(config_dir=config_dir, credential=credential)
    if config is None:
        raise RuntimeError("Missing optimization config; package .agent_configs/baseline/")
    if not config.model or not config.model.strip():
        raise ValueError("Optimization config requires a model deployment name")
    if not config.instructions or not config.instructions.strip():
        raise ValueError("Optimization config requires non-empty instructions")
    if config.has_skills or config.tool_definitions:
        raise ValueError("Fibey optimization supports instructions and model only; keep toolbox skills and tools unchanged")
    requested = os.getenv("OPTIMIZATION_CANDIDATE_ID", "").strip()
    if requested and config.source.startswith("local:"):
        if Path(config.source.removeprefix("local:")).name != requested:
            raise RuntimeError("Requested optimization candidate was not loaded; refusing baseline fallback")
    elif requested and config.candidate_id != requested and config.source != "env:OPTIMIZATION_CONFIG":
        raise RuntimeError("Requested optimization candidate was not loaded")
    return config


async def _serve() -> None:
    sensitive = os.getenv("ENABLE_SENSITIVE_TELEMETRY", "false").strip().lower() == "true"
    configure_otel_providers(
        enable_sensitive_data=sensitive,
        enable_message_events=sensitive,
    )
    logger.info("OpenTelemetry enabled; sensitive content tracing=%s", sensitive)
    config = await asyncio.to_thread(_load_optimization_config)

    async with AsyncExitStack() as resources:
        credential = await resources.enter_async_context(DefaultAzureCredential())
        project = await resources.enter_async_context(AIProjectClient(
            endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            credential=credential,
        ))
        client = FoundryChatClient(
            project_client=project,
            model=config.model,
        )
        resources.push_async_callback(client.client.close)
        # The SDK forwards per-request platform context (including call-id) and
        # refreshes credentials. Do not replace this with custom bearer auth.
        toolbox = FoundryToolbox(credential)
        resources.push_async_callback(toolbox.close)
        skills = SkillsProvider(
            CachingSkillsSource(FibeySkillsSource(
                toolbox, os.getenv("SKILLS_SOURCE", "auto").strip().lower()
            )),
            disable_load_skill_approval=True,
            disable_read_skill_resource_approval=True,
        )
        agent = Agent(
            client=client,
            name="fibey",
            instructions=config.compose_instructions(),
            tools=toolbox,
            context_providers=[skills],
            default_options={
                "store": False,
                **({"temperature": config.temperature} if config.temperature is not None else {}),
            },
        )
        # The host owns agent/tool lifecycle and retrieves history from Foundry.
        # History retrieval failures must fail the turn, not silently erase context.
        await ResponsesHostServer(agent).run_async()


def main() -> None:
    asyncio.run(_serve())


if __name__ == "__main__":
    main()
