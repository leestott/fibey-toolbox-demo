import os
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from agent_framework import InlineSkill, SkillFrontmatter, SkillsSourceContext

from fibey.agent import hosted


OPTIMIZATION_ENV = {
    "OPTIMIZATION_CONFIG": "",
    "OPTIMIZATION_CANDIDATE_ID": "",
    "OPTIMIZATION_RESOLVE_ENDPOINT": "",
    "OPTIMIZATION_LOCAL_DIR": "",
}


class HostedOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, OPTIMIZATION_ENV)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_baseline_preserves_existing_prompt_model_and_tool_skill_boundaries(self):
        config = hosted._load_optimization_config()
        original = Path(hosted.__file__).parent / "prompts" / "system_prompt.md"
        self.assertEqual(config.instructions, original.read_text(encoding="utf-8").strip())
        self.assertEqual(config.model, "gpt-5.4-mini")
        self.assertIsNone(config.temperature)
        self.assertFalse(config.has_skills)
        self.assertEqual(config.tool_definitions, [])

    def test_inline_candidate_overrides_baseline_and_closes_resolver_credential(self):
        candidate = {"model": "candidate-model", "instructions": "Candidate instructions"}
        with (
            patch.dict(os.environ, {"OPTIMIZATION_CONFIG": json.dumps(candidate)}),
            patch.object(hosted, "SyncDefaultAzureCredential") as credential_factory,
        ):
            config = hosted._load_optimization_config()
        self.assertEqual(config.model, "candidate-model")
        self.assertEqual(config.compose_instructions(), "Candidate instructions")
        credential_factory.return_value.__exit__.assert_called_once()

    def test_invalid_inline_candidate_fails_without_baseline_fallback(self):
        with patch.dict(os.environ, {"OPTIMIZATION_CONFIG": "{invalid"}):
            with self.assertRaises(ValueError):
                hosted._load_optimization_config()

    def test_missing_model_or_instructions_fail_explicitly(self):
        for candidate in (
            {"instructions": "Instructions"},
            {"model": "model"},
            {"model": "model", "instructions": " "},
        ):
            with self.subTest(candidate=candidate):
                with patch.dict(os.environ, {"OPTIMIZATION_CONFIG": json.dumps(candidate)}):
                    with self.assertRaises(ValueError):
                        hosted._load_optimization_config()

    def test_missing_config_fails_explicitly(self):
        with TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"OPTIMIZATION_LOCAL_DIR": directory}):
                with self.assertRaisesRegex(RuntimeError, "Missing optimization config"):
                    hosted._load_optimization_config()

    def test_missing_local_candidate_does_not_evaluate_baseline_as_candidate(self):
        with patch.dict(os.environ, {"OPTIMIZATION_CANDIDATE_ID": "missing-candidate"}):
            with self.assertRaisesRegex(RuntimeError, "refusing baseline fallback"):
                hosted._load_optimization_config()

    def test_skill_and_tool_candidates_are_rejected_instead_of_ignored(self):
        for extra in (
            {"skills": [{"name": "new-skill", "description": "Skill", "body": "Instructions"}]},
            {"tools": [{"type": "function", "function": {"name": "replacement"}}]},
        ):
            candidate = {"model": "model", "instructions": "Instructions", **extra}
            with self.subTest(extra=extra):
                with patch.dict(os.environ, {"OPTIMIZATION_CONFIG": json.dumps(candidate)}):
                    with self.assertRaisesRegex(ValueError, "keep toolbox skills and tools unchanged"):
                        hosted._load_optimization_config()


class HostedSkillsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.source = hosted.FibeySkillsSource(SimpleNamespace(session=None))
        self.context = SkillsSourceContext(agent=MagicMock())

    async def test_bundled_skills_are_available_without_published_skills(self):
        self.source.published.get_skills = AsyncMock(return_value=[])
        skills = await self.source.get_skills(self.context)
        self.assertEqual({skill.frontmatter.name for skill in skills}, {
            "inventory-lookup", "work-order-management", "knowledge-retrieval",
            "work-order-preparation", "field-briefing",
        })

    async def test_remote_failure_falls_back_without_logging_private_details(self):
        self.source.published.get_skills = AsyncMock(side_effect=RuntimeError("private endpoint detail"))
        with self.assertLogs(hosted.logger, level="WARNING") as logs:
            skills = await self.source.get_skills(self.context)
        self.assertEqual(len(skills), 5)
        self.assertNotIn("private endpoint detail", str(logs.output))

    async def test_published_skill_overrides_without_discarding_other_skills(self):
        published = InlineSkill(
            frontmatter=SkillFrontmatter(name="inventory-lookup", description="Published inventory skill"),
            instructions="Published instructions",
        )
        self.source.published.get_skills = AsyncMock(return_value=[published])
        skills = await self.source.get_skills(self.context)
        self.assertEqual(len(skills), 5)
        self.assertIs(next(skill for skill in skills if skill.frontmatter.name == "inventory-lookup"), published)

    async def test_file_mode_never_requests_published_skills(self):
        self.source.mode = "file"
        self.source.published.get_skills = AsyncMock(side_effect=AssertionError("Unexpected MCP request"))
        self.assertEqual(len(await self.source.get_skills(self.context)), 5)
        self.source.published.get_skills.assert_not_awaited()

    async def test_missing_bundled_skills_fail_instead_of_silently_disappearing(self):
        self.source.bundled.get_skills = AsyncMock(return_value=[])
        with self.assertRaisesRegex(RuntimeError, "Bundled Fibey skills are missing"):
            await self.source.get_skills(self.context)

    async def test_explicit_mcp_mode_fails_if_no_skills_published(self):
        self.source.mode = "mcp"
        self.source.published.get_skills = AsyncMock(return_value=[])
        with self.assertRaisesRegex(RuntimeError, "requires published"):
            await self.source.get_skills(self.context)

    def test_invalid_skill_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            hosted.FibeySkillsSource(SimpleNamespace(session=None), "typo")

    def test_session_provider_uses_current_authenticated_toolbox_session(self):
        first, second = object(), object()
        with self.assertRaises(RuntimeError):
            self.source._session()
        self.source.toolbox.session = first
        self.assertIs(self.source._session(), first)
        self.source.toolbox.session = second
        self.assertIs(self.source._session(), second)


class HostedLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, OPTIMIZATION_ENV)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    async def test_server_uses_supported_host_and_closes_all_resources_on_failure(self):
        credential = AsyncMock()
        credential.__aenter__.return_value = credential
        project = AsyncMock()
        project.__aenter__.return_value = project
        client = SimpleNamespace(client=SimpleNamespace(close=AsyncMock()))
        toolbox = SimpleNamespace(session=None, close=AsyncMock())
        server = SimpleNamespace(run_async=AsyncMock(side_effect=RuntimeError("server stopped")))
        with (
            patch.dict(os.environ, {
                "FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/fibey",
                "AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-5.4-mini",
                "ENABLE_SENSITIVE_TELEMETRY": "false",
                "SKILLS_SOURCE": "file",
            }),
            patch.object(hosted, "configure_otel_providers") as telemetry,
            patch.object(hosted, "DefaultAzureCredential", return_value=credential),
            patch.object(hosted, "AIProjectClient", return_value=project),
            patch.object(hosted, "FoundryChatClient", return_value=client),
            patch.object(hosted, "FoundryToolbox", return_value=toolbox) as toolbox_factory,
            patch.object(hosted, "Agent") as agent_factory,
            patch.object(hosted, "ResponsesHostServer", return_value=server) as server_factory,
        ):
            with self.assertRaisesRegex(RuntimeError, "server stopped"):
                await hosted._serve()
            telemetry.assert_called_once_with(enable_sensitive_data=False, enable_message_events=False)
            toolbox_factory.assert_called_once_with(credential)
            server_factory.assert_called_once_with(agent_factory.return_value)
            options = agent_factory.call_args.kwargs
            self.assertEqual(options["default_options"], {"store": False})
            self.assertIs(options["tools"], toolbox)
            self.assertEqual(options["instructions"], hosted._load_optimization_config().compose_instructions())
            self.assertEqual(len(options["context_providers"]), 1)
        server.run_async.assert_awaited_once()
        toolbox.close.assert_awaited_once()
        client.client.close.assert_awaited_once()
        project.__aexit__.assert_awaited_once()
        credential.__aexit__.assert_awaited_once()

    async def test_real_foundry_client_can_be_constructed_and_closed_without_cloud(self):
        captured = []

        def server_factory(agent):
            captured.append(agent)
            return SimpleNamespace(run_async=AsyncMock())

        with (
            patch.dict(os.environ, {
                "FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/fibey",
                "AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-5.4-mini",
                "TOOLBOX_NAME": "fibey-toolbox",
                "SKILLS_SOURCE": "file",
                "ENABLE_SENSITIVE_TELEMETRY": "true",
            }),
            patch.object(hosted, "configure_otel_providers") as telemetry,
            patch.object(hosted, "ResponsesHostServer", side_effect=server_factory),
        ):
            await hosted._serve()
            telemetry.assert_called_once_with(enable_sensitive_data=True, enable_message_events=True)
        self.assertTrue(captured[0].client.client.is_closed())
        self.assertIsInstance(captured[0].mcp_tools[0], hosted.FoundryToolbox)

    async def test_host_consumes_candidate_model_instructions_and_optional_temperature(self):
        config = hosted.OptimizationConfig(
            model="candidate-model", instructions="Candidate instructions", temperature=1.0,
        )
        credential = AsyncMock()
        credential.__aenter__.return_value = credential
        project = AsyncMock()
        project.__aenter__.return_value = project
        client = SimpleNamespace(client=SimpleNamespace(close=AsyncMock()))
        toolbox = SimpleNamespace(session=None, close=AsyncMock())
        with (
            patch.object(hosted, "_load_optimization_config", return_value=config),
            patch.object(hosted, "configure_otel_providers"),
            patch.dict(os.environ, {"FOUNDRY_PROJECT_ENDPOINT": "https://example.test", "SKILLS_SOURCE": "file"}),
            patch.object(hosted, "DefaultAzureCredential", return_value=credential),
            patch.object(hosted, "AIProjectClient", return_value=project),
            patch.object(hosted, "FoundryChatClient", return_value=client) as client_factory,
            patch.object(hosted, "FoundryToolbox", return_value=toolbox),
            patch.object(hosted, "Agent") as agent_factory,
            patch.object(hosted, "ResponsesHostServer") as server_factory,
        ):
            server_factory.return_value.run_async = AsyncMock()
            await hosted._serve()
        self.assertEqual(client_factory.call_args.kwargs["model"], "candidate-model")
        options = agent_factory.call_args.kwargs
        self.assertEqual(options["instructions"], "Candidate instructions")
        self.assertEqual(options["default_options"], {"store": False, "temperature": 1.0})
        self.assertIs(options["tools"], toolbox)


if __name__ == "__main__":
    unittest.main()
