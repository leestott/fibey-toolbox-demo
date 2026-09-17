import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from agent_framework import InlineSkill, SkillFrontmatter, SkillsSourceContext

from fibey.agent import hosted


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
            self.assertEqual(options["instructions"], hosted._load_system_prompt())
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


if __name__ == "__main__":
    unittest.main()
