import asyncio
import json
import os
import unittest
import uuid
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fibey.gateway import api_server as gateway


PROJECT = "https://example.services.ai.azure.com/api/projects/fibey"
SESSION = "11111111-1111-4111-8111-111111111111"
COMPUTE_SESSION = "abcdefghijklmnopqrstuvwxy"


def frame(event_type, **data):
    return f"data: {json.dumps({'type': event_type, **data})}\n\n".encode()


class Upstream(httpx.AsyncByteStream):
    def __init__(self, chunks, stay_open=False):
        self.chunks = chunks
        self.stay_open = stay_open
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        if self.stay_open:
            await asyncio.sleep(60)

    async def aclose(self):
        self.closed = True


async def collect(stream):
    return "".join([event async for event in stream])


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = patch.multiple(
            gateway, AGENT_MODE="hosted", HOSTED_AGENT_ENDPOINT=PROJECT,
            HOSTED_AGENT_NAME="fibey-agent", HOSTED_AGENT_RESPONSES_URL="",
            CONTAINERAPP_AGENT_URL="https://agent.example",
        )
        self.config.start()
        self.addCleanup(self.config.stop)
        gateway.sessions.clear()
        gateway._hosted_sessions.clear()
        gateway._hosted_compute_sessions.clear()
        gateway._active_sessions.clear()
        gateway.app.state.token_provider = AsyncMock(return_value="test-token")
        self.browser = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=gateway.app), base_url="http://gateway"
        )
        self.addAsyncCleanup(self.browser.aclose)
        self.requests = []

    async def upstream(self, chunks, *, status=200, stay_open=False, session_header=COMPUTE_SESSION):
        stream = Upstream(chunks, stay_open)

        def respond(request):
            self.requests.append(request)
            headers = {"Content-Type": "text/event-stream"}
            if session_header is not None:
                headers["x-agent-session-id"] = session_header
            return httpx.Response(status, stream=stream, headers=headers)

        client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        gateway.app.state.http_client = client
        self.addAsyncCleanup(client.aclose)
        return stream

    async def test_completed_terminates_without_waiting_for_done_or_socket_close(self):
        upstream = await self.upstream([
            frame("response.output_text.delta", delta="Hello"),
            frame("response.completed", response={"id": "resp_1", "status": "completed"}),
        ], stay_open=True)
        result = await asyncio.wait_for(collect(gateway._run_hosted("Hi", SESSION)), 2)
        self.assertIn('"content": "Hello"', result)
        self.assertNotIn("event: error", result)
        self.assertEqual(result.count("event: done"), 1)
        self.assertEqual(gateway._hosted_sessions[SESSION], "resp_1")
        self.assertTrue(upstream.closed)
        self.assertEqual(self.requests[0].headers["Authorization"], "Bearer test-token")

    async def test_previous_response_used_only_after_success(self):
        gateway._hosted_sessions[SESSION] = "resp_previous"
        gateway._hosted_compute_sessions[SESSION] = COMPUTE_SESSION
        await self.upstream([frame("response.completed", response={"id": "resp_next"})])
        await collect(gateway._run_hosted("Follow up", SESSION))
        self.assertEqual(json.loads(self.requests[0].content)["previous_response_id"], "resp_previous")
        self.assertEqual(gateway._hosted_sessions[SESSION], "resp_next")
        self.assertEqual(json.loads(self.requests[0].content)["agent_session_id"], COMPUTE_SESSION)

    async def test_v1_first_turn_uses_server_assigned_session_not_browser_uuid(self):
        await self.upstream([frame("response.completed", response={"id": "resp_first"})])
        result = await collect(gateway._run_hosted("Hi", SESSION))
        request = self.requests[0]
        self.assertEqual(request.url.params["api-version"], "v1")
        self.assertEqual(json.loads(request.content), {"input": "Hi", "stream": True, "store": True})
        self.assertNotIn("x-agent-session-id", request.headers)
        self.assertNotIn("Foundry-Features", request.headers)
        self.assertEqual(request.headers["Accept"], "text/event-stream")
        self.assertEqual(gateway._hosted_compute_sessions[SESSION], COMPUTE_SESSION)
        self.assertNotIn("event: error", result)

    async def test_compute_session_is_reused_across_turns(self):
        await self.upstream([frame("response.completed", response={"id": "resp_first"})])
        await collect(gateway._run_hosted("First", SESSION))
        await self.upstream([frame("response.completed", response={"id": "resp_second"})])
        result = await collect(gateway._run_hosted("Second", SESSION))
        body = json.loads(self.requests[-1].content)
        self.assertEqual(body["agent_session_id"], COMPUTE_SESSION)
        self.assertEqual(body["previous_response_id"], "resp_first")
        self.assertEqual(gateway._hosted_sessions[SESSION], "resp_second")
        self.assertNotIn("event: error", result)

    async def test_distinct_browser_sessions_do_not_share_history_or_compute(self):
        other_session = str(uuid.uuid4())
        await self.upstream([frame("response.completed", response={"id": "resp_first"})])
        await collect(gateway._run_hosted("First browser", SESSION))
        await self.upstream([frame("response.completed", response={"id": "resp_other"})],
                            session_header="other-compute-session")
        await collect(gateway._run_hosted("Other browser", other_session))
        self.assertNotIn("agent_session_id", json.loads(self.requests[-1].content))
        self.assertNotIn("previous_response_id", json.loads(self.requests[-1].content))
        await self.upstream([frame("response.completed", response={"id": "resp_next"})])
        await collect(gateway._run_hosted("First browser again", SESSION))
        body = json.loads(self.requests[-1].content)
        self.assertEqual(body["agent_session_id"], COMPUTE_SESSION)
        self.assertEqual(body["previous_response_id"], "resp_first")
        self.assertEqual(gateway._hosted_compute_sessions[other_session], "other-compute-session")

    async def test_response_payload_can_supply_compute_session_without_header(self):
        await self.upstream([frame("response.completed", response={
            "id": "resp_first", "agent_session_id": COMPUTE_SESSION,
        })], session_header=None)
        result = await collect(gateway._run_hosted("Hi", SESSION))
        self.assertEqual(gateway._hosted_compute_sessions[SESSION], COMPUTE_SESSION)
        self.assertNotIn("event: error", result)

    async def test_session_from_created_event_survives_truncation_without_advancing_history(self):
        await self.upstream([frame("response.created", response={
            "id": "resp_partial", "agent_session_id": COMPUTE_SESSION,
        })], session_header=None)
        result = await collect(gateway._run_hosted("Hi", SESSION))
        self.assertEqual(gateway._hosted_compute_sessions[SESSION], COMPUTE_SESSION)
        self.assertNotIn(SESSION, gateway._hosted_sessions)
        self.assertIn("event: error", result)
        self.assertEqual(len(self.requests), 1)

    async def test_missing_or_invalid_compute_session_is_not_successful(self):
        for compute_id in (None, "", 123, "x" * 257):
            with self.subTest(compute_id_type=type(compute_id)):
                await self.upstream([frame("response.completed", response={
                    "id": "resp_first", "agent_session_id": compute_id,
                })], session_header=None)
                result = await collect(gateway._run_hosted("Hi", SESSION))
                self.assertIn("event: error", result)
                self.assertNotIn(SESSION, gateway._hosted_sessions)
                self.assertNotIn(SESSION, gateway._hosted_compute_sessions)

    async def test_completion_requires_response_id_for_conversation_continuity(self):
        await self.upstream([frame("response.completed", response={"status": "completed"})])
        result = await collect(gateway._run_hosted("Hi", SESSION))
        self.assertIn("event: error", result)
        self.assertNotIn(SESSION, gateway._hosted_sessions)
        self.assertEqual(gateway._hosted_compute_sessions[SESSION], COMPUTE_SESSION)

    async def test_mismatched_compute_session_does_not_overwrite_existing_state(self):
        gateway._hosted_compute_sessions[SESSION] = COMPUTE_SESSION
        gateway._hosted_sessions[SESSION] = "resp_previous"
        for session_header, payload_id in (("different-session", None), (COMPUTE_SESSION, "different-session")):
            with self.subTest(session_header=session_header):
                await self.upstream([frame("response.completed", response={
                    "id": "resp_next", "agent_session_id": payload_id,
                })], session_header=session_header)
                result = await collect(gateway._run_hosted("Hi", SESSION))
                self.assertIn("event: error", result)
                self.assertNotIn("different-session", result)
                self.assertEqual(gateway._hosted_compute_sessions[SESSION], COMPUTE_SESSION)
                self.assertEqual(gateway._hosted_sessions[SESSION], "resp_previous")

    async def test_failure_events_terminate_and_preserve_previous_response(self):
        for kind in ("response.failed", "response.incomplete", "response.cancelled", "error"):
            with self.subTest(kind=kind):
                gateway._hosted_sessions[SESSION] = "resp_previous"
                await self.upstream([frame(
                    kind, response={"error": {"message": "private upstream detail"}}
                )], stay_open=True)
                with self.assertLogs(gateway.logger, level="ERROR") as logs:
                    result = await asyncio.wait_for(collect(gateway._run_hosted("Hi", SESSION)), 2)
                self.assertEqual(result.count("event: error"), 1)
                self.assertEqual(result.count("event: done"), 1)
                self.assertNotIn("private upstream detail", result + str(logs.output))
                self.assertEqual(gateway._hosted_sessions[SESSION], "resp_previous")

    async def test_truncated_and_malformed_streams_report_error(self):
        for chunks in (
            [], [frame("response.output_text.delta", delta="Partial")],
            [b"data: [DONE]\n\n"],
            [b'data: {"type":"response.completed"}\n'],
            [b"data: malformed-private-content\n\n"],
        ):
            with self.subTest(chunks=chunks):
                await self.upstream(chunks)
                result = await collect(gateway._run_hosted("Hi", SESSION))
                self.assertEqual(result.count("event: error"), 1)
                self.assertEqual(result.count("event: done"), 1)
                self.assertNotIn(SESSION, gateway._hosted_sessions)
                self.assertNotIn("malformed-private-content", result)

    async def test_crlf_multiline_and_split_utf8_frames(self):
        payload = (
            ': heartbeat\r\n\r\nevent: response.output_text.delta\r\n'
            'data: {"delta":\r\ndata: "café"}\r\n\r\n'
        ).encode()
        await self.upstream(
            [payload[i:i + 3] for i in range(0, len(payload), 3)]
            + [frame("response.completed", response={"id": "resp_1"})]
        )
        result = await collect(gateway._run_hosted("Hi", SESSION))
        self.assertIn('"content": "caf\\u00e9"', result)
        self.assertNotIn("event: error", result)

    async def test_activity_and_citation_events_are_preserved(self):
        item = {"type": "mcp_call", "id": "call_1", "name": "inventory", "arguments": "{}"}
        await self.upstream([
            frame("response.output_item.added", item=item),
            frame("response.output_item.added", item=item),
            frame("response.output_item.done", item={**item, "output": "In stock"}),
            frame("response.output_text.annotation.added", annotation={
                "title": "Guide", "url": "https://example.com/guide",
            }),
            frame("response.completed", response={"id": "resp_1"}),
        ])
        result = await collect(gateway._run_hosted("Hi", SESSION))
        self.assertEqual(result.count("event: activity"), 2)
        for text in ('"status": "running"', '"status": "complete"', "In stock", "event: citation"):
            self.assertIn(text, result)

    async def test_http_errors_do_not_leak_upstream_body(self):
        await self.upstream([b"private upstream message"], status=403)
        with self.assertLogs(gateway.logger, level="ERROR") as logs:
            result = await collect(gateway._run_hosted("Hi", SESSION))
        self.assertIn("HTTP 403", result)
        self.assertNotIn("private upstream message", result + str(logs.output))
        self.assertEqual(result.count("event: done"), 1)

    async def test_token_failure_is_sanitized(self):
        gateway.app.state.token_provider.side_effect = RuntimeError("private credential details")
        with self.assertLogs(gateway.logger, level="ERROR") as logs:
            result = await collect(gateway._run_hosted("Hi", SESSION))
        self.assertIn("event: error", result)
        self.assertNotIn("private credential details", result + str(logs.output))

    async def test_upstream_timeout_reports_error_and_done(self):
        def timeout(request):
            raise httpx.ReadTimeout("private transport details")

        client = httpx.AsyncClient(transport=httpx.MockTransport(timeout))
        gateway.app.state.http_client = client
        self.addAsyncCleanup(client.aclose)
        for runner in (gateway._run_hosted, gateway._run_containerapp):
            result = await collect(runner("Hi", SESSION))
            self.assertIn("timed out", result)
            self.assertEqual(result.count("event: error"), 1)
            self.assertEqual(result.count("event: done"), 1)
            self.assertNotIn("private transport details", result)

    async def test_container_relay_preserves_delimiters_and_single_done(self):
        payload = gateway._sse("delta", {"content": "Hello"}) + gateway._sse("done", "[DONE]")
        upstream = await self.upstream([payload.encode()], stay_open=True)
        result = await asyncio.wait_for(collect(gateway._run_containerapp("Hi", SESSION)), 2)
        self.assertEqual(result, payload)
        self.assertTrue(upstream.closed)

    async def test_container_truncation_is_not_reported_as_success(self):
        await self.upstream([gateway._sse("delta", {"content": "Partial"}).encode()])
        result = await collect(gateway._run_containerapp("Hi", SESSION))
        self.assertEqual(result.count("event: error"), 1)
        self.assertEqual(result.count("event: done"), 1)

    async def test_chat_validates_message_and_uuid_before_starting_stream(self):
        for body in (
            {}, {"message": ""}, {"message": " \n "}, {"message": 123},
            {"message": "x" * 16_001}, {"message": "Hi", "session_id": "../../x"},
            {"message": "Hi", "session_id": None}, {"message": "Hi", "extra": "not accepted"},
        ):
            with self.subTest(body_type=str(type(body))):
                response = await self.browser.post("/api/chat", json=body)
                self.assertEqual(response.status_code, 422)
        self.assertFalse(gateway._active_sessions)

    async def test_chat_generates_session_header_and_does_not_log_message(self):
        await self.upstream([frame("response.completed", response={"id": "resp_1"})])
        with self.assertLogs(gateway.logger, level="INFO") as logs:
            response = await self.browser.post("/api/chat", json={"message": "private technician message"})
        self.assertEqual(response.status_code, 200)
        uuid.UUID(response.headers["X-Session-Id"])
        self.assertEqual(response.headers["X-Accel-Buffering"], "no")
        self.assertNotIn("private technician message", str(logs.output))
        self.assertFalse(gateway._active_sessions)

    async def test_reset_clears_history_and_requests_a_fresh_compute_session(self):
        gateway.sessions[SESSION] = {"history": ["old"]}
        gateway._hosted_sessions[SESSION] = "resp_previous"
        gateway._hosted_compute_sessions[SESSION] = COMPUTE_SESSION
        response = await self.browser.post("/api/sessions/reset", json={"session_id": SESSION})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION, gateway.sessions)
        self.assertNotIn(SESSION, gateway._hosted_sessions)
        self.assertNotIn(SESSION, gateway._hosted_compute_sessions)
        await self.upstream([frame("response.completed", response={"id": "resp_new"})],
                            session_header="new-compute-session")
        result = await collect(gateway._run_hosted("Fresh start", SESSION))
        body = json.loads(self.requests[-1].content)
        self.assertNotIn("agent_session_id", body)
        self.assertNotIn("previous_response_id", body)
        self.assertEqual(gateway._hosted_compute_sessions[SESSION], "new-compute-session")
        self.assertNotIn("event: error", result)

    async def test_concurrent_turn_and_reset_are_rejected(self):
        gateway._active_sessions.add(SESSION)
        for path, body in (
            ("/api/chat", {"message": "Hi", "session_id": SESSION}),
            ("/api/sessions/reset", {"session_id": SESSION}),
        ):
            response = await self.browser.post(path, json=body)
            self.assertEqual(response.status_code, 409)

    async def test_lifespan_reuses_and_closes_async_credentials_and_http_client(self):
        credential = AsyncMock()
        credential.__aenter__.return_value = credential
        provider = AsyncMock(return_value="cached-token")
        with patch.object(gateway, "DefaultAzureCredential", return_value=credential) as factory:
            with patch.object(gateway, "get_bearer_token_provider", return_value=provider):
                async with gateway.lifespan(gateway.app):
                    client = gateway.app.state.http_client
                    self.assertEqual(await gateway._get_hosted_token(), "cached-token")
                    self.assertEqual(await gateway._get_hosted_token(), "cached-token")
                    self.assertFalse(client.is_closed)
                self.assertTrue(client.is_closed)
                factory.assert_called_once()
                credential.__aexit__.assert_awaited_once()

    async def test_invalid_mode_fails_closed(self):
        with patch.object(gateway, "AGENT_MODE", "typo"):
            with self.assertRaises(ValueError):
                async with gateway.lifespan(gateway.app):
                    pass
            response = await self.browser.post("/api/chat", json={"message": "Hi"})
            self.assertEqual(response.status_code, 503)

    async def test_cors_accepts_only_configured_origin_and_exposes_session_header(self):
        app = FastAPI()
        middleware = next(m for m in gateway.app.user_middleware if m.cls is CORSMiddleware)
        app.add_middleware(middleware.cls, **{
            **middleware.kwargs, "allow_origins": ["https://ui.example"],
        })

        @app.post("/chat")
        def respond():
            return {}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gateway") as client:
            for origin, status in (("https://ui.example", 200), ("https://other.example", 400)):
                response = await client.options("/chat", headers={
                    "Origin": origin, "Access-Control-Request-Method": "POST",
                })
                self.assertEqual(response.status_code, status)
            response = await client.post("/chat", headers={"Origin": "https://ui.example"})
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "https://ui.example")
            self.assertEqual(response.headers["Access-Control-Expose-Headers"], "X-Session-Id")


class ConfigurationTests(unittest.TestCase):
    def test_function_outputs_and_mcp_lifecycle_keep_call_ids(self):
        output = gateway._hosted_activity("response.output_item.done", {"item": {
            "type": "function_call_output", "call_id": "call_1", "output": {"stock": 5},
        }}, set())
        self.assertEqual(output["call_id"], "call_1")
        self.assertEqual(output["status"], "complete")
        self.assertIn('"stock": 5', output["result"])
        failed = gateway._hosted_activity("response.mcp_call.failed", {"item_id": "call_2"}, set())
        self.assertEqual(failed["call_id"], "call_2")
        self.assertEqual(failed["status"], "error")

    def test_project_and_exact_response_urls(self):
        exact = f"{PROJECT}/agents/fibey-agent/endpoint/protocols/openai/responses"
        with patch.multiple(gateway, HOSTED_AGENT_ENDPOINT=PROJECT + "/", HOSTED_AGENT_NAME="fibey-agent",
                            HOSTED_AGENT_RESPONSES_URL=""):
            self.assertEqual(gateway._hosted_responses_url(), exact + "?api-version=v1")
            with patch.object(gateway, "HOSTED_AGENT_ENDPOINT", exact):
                self.assertEqual(gateway._hosted_responses_url(), exact + "?api-version=v1")
            with patch.object(gateway, "HOSTED_AGENT_RESPONSES_URL", exact + "?api-version=custom"):
                self.assertEqual(gateway._hosted_responses_url(), exact + "?api-version=custom")
            for invalid in ("http://example.com/responses", "https://user:password@example.com/responses",
                            "https://example.com/responses#fragment", PROJECT):
                with patch.object(gateway, "HOSTED_AGENT_RESPONSES_URL", invalid):
                    with self.assertRaises(ValueError):
                        gateway._hosted_responses_url()

    def test_cors_configuration_rejects_wildcards_and_paths(self):
        for invalid in ("*", "https://*.example.com", "https://ui.example/path", "https://user@ui.example"):
            with patch.dict(os.environ, {"CORS_ORIGINS": invalid}):
                with self.assertRaises(ValueError):
                    gateway._cors_origins()
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://ui.example, http://localhost:5173/"}):
            self.assertEqual(gateway._cors_origins(), ["https://ui.example", "http://localhost:5173"])


if __name__ == "__main__":
    unittest.main()
