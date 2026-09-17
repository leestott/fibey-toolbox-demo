import io
import json
import os
import unittest
from contextlib import asynccontextmanager, redirect_stdout
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from azure.identity import AzureCliCredential

from fibey.agent import agent as local
from fibey.agent import main, service


class FakeAgent:
    def __init__(self):
        self.sessions = []

    def run(self, message, *, stream, session):
        self.sessions.append(session)

        async def updates():
            contents = [
                SimpleNamespace(
                    type="function_call", name="call_tool", call_id="call_1",
                    arguments=json.dumps({
                        "name": "inventory___check_stock", "arguments": {"part_id": "FIB-001"},
                    }),
                ),
                SimpleNamespace(type="function_result", call_id="call_1", result={"stock": 5}),
                SimpleNamespace(type="text", text="Five in stock."),
            ]
            for content in contents:
                yield SimpleNamespace(contents=[content])

        return updates()


class LocalRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_string_tool_arguments_stream_and_sessions_survive_new_agents(self):
        agent = FakeAgent()

        @asynccontextmanager
        async def create():
            yield agent, []

        session = {}
        with patch.object(local, "create_agent", create):
            with self.assertLogs(local.logger, level="INFO") as logs:
                events = [event async for event in local.run_agent("Check stock", session)]
                await anext(local.run_agent("Follow up", session))
        self.assertIs(agent.sessions[0], agent.sessions[1])
        activities = [event for event in events if event["type"] == "activity"]
        self.assertTrue(any(event["tool"] == "inventory___check_stock" for event in activities))
        self.assertEqual(activities[-1]["status"], "complete")
        self.assertEqual(events[-1], {"type": "delta", "content": "Five in stock."})
        self.assertNotIn("preview=", str(logs.output))
        self.assertNotIn('"stock": 5', str(logs.output))

    async def test_bundled_skills_do_not_require_an_unimplemented_approval_ui(self):
        with patch.dict(os.environ, {"SKILLS_SOURCE": "file", "TOOLBOX_MCP_URL": ""}):
            with patch.object(local, "SkillsProvider", wraps=local.SkillsProvider) as constructor:
                await local._build_skills_provider(MagicMock())
        self.assertTrue(constructor.call_args.kwargs["disable_load_skill_approval"])
        self.assertTrue(constructor.call_args.kwargs["disable_read_skill_resource_approval"])

    async def test_strict_mcp_mode_never_silently_drops_skills(self):
        with patch.dict(os.environ, {"SKILLS_SOURCE": "mcp", "TOOLBOX_MCP_URL": ""}):
            with self.assertRaisesRegex(RuntimeError, "requires a toolbox URL"):
                await local._build_skills_provider(MagicMock())

    async def test_real_current_foundry_client_construction_and_cleanup(self):
        credential = AzureCliCredential()
        with (
            patch.dict(os.environ, {
                "FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/fibey",
                "FOUNDRY_MODEL": "gpt-5.4-mini", "SKILLS_SOURCE": "file", "TOOLBOX_MCP_URL": "",
            }),
            patch.object(local, "_get_credential", return_value=credential),
            patch.object(credential, "close", wraps=credential.close) as close,
        ):
            async with local.create_agent() as (agent, tools):
                self.assertEqual(agent.default_options["store"], False)
                self.assertEqual(agent.client.model, "gpt-5.4-mini")
                self.assertEqual(tools, [])
                self.assertFalse(agent.client.client.is_closed())
            self.assertTrue(agent.client.client.is_closed())
            close.assert_called_once()

    async def test_clients_close_when_skills_initialization_fails(self):
        credential = MagicMock()
        client = SimpleNamespace(
            client=SimpleNamespace(close=AsyncMock()),
            project_client=SimpleNamespace(close=AsyncMock()),
        )
        with (
            patch.object(local, "_get_credential", return_value=credential),
            patch.object(local, "FoundryChatClient", return_value=client),
            patch.object(local, "_create_toolbox_mcp", return_value=None),
            patch.object(local, "_create_kb_search_tool", return_value=None),
            patch.object(local, "_build_skills_provider", side_effect=RuntimeError("bad skills")),
        ):
            with self.assertRaisesRegex(RuntimeError, "bad skills"):
                async with local.create_agent():
                    pass
        client.client.close.assert_awaited_once()
        client.project_client.close.assert_awaited_once()
        credential.close.assert_called_once()

    async def test_legacy_service_stream_contract(self):
        async def run(message, session):
            yield {"type": "delta", "content": "Hello"}
            yield {"type": "activity", "tool": "inventory", "status": "complete"}

        with patch.object(local, "run_agent", run):
            result = "".join([event async for event in service._run_agent_stream("Hi", "test-session")])
        self.assertIn("event: delta\n", result)
        self.assertIn("event: activity\n", result)
        self.assertEqual(result.count("event: done\n"), 1)

    async def test_cli_runs_with_same_generator_contract(self):
        async def run(message, session):
            yield {"type": "delta", "content": "Hello"}

        output = io.StringIO()
        with (
            patch("builtins.input", side_effect=["Hi", "quit"]),
            patch.object(local, "run_agent", run),
            redirect_stdout(output),
        ):
            await main.main()
        self.assertIn("Fibey: Hello", output.getvalue())


if __name__ == "__main__":
    unittest.main()
