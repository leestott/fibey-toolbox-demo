import os
import uuid
import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

import httpx
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.getLogger("fibey").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# In-memory session store
sessions: dict[str, dict] = {}

AGENT_MODE = os.getenv("AGENT_MODE", "local").strip().lower()
SUPPORTED_MODES = {"local", "hosted", "containerapp"}

# Hosted agent config
HOSTED_AGENT_ENDPOINT = os.getenv("HOSTED_AGENT_ENDPOINT", "")
HOSTED_AGENT_NAME = os.getenv("HOSTED_AGENT_NAME", "fibey-agent")
HOSTED_AGENT_RESPONSES_URL = os.getenv("HOSTED_AGENT_RESPONSES_URL", "")
HOSTED_API_VERSION = "v1"

# Container App agent service config
CONTAINERAPP_AGENT_URL = os.getenv("CONTAINERAPP_AGENT_URL", "")

# Conversation history and sandbox affinity are separate Foundry identifiers.
_hosted_sessions: dict[str, str] = {}
_hosted_compute_sessions: dict[str, str] = {}
_active_sessions: set[str] = set()


def _hosted_responses_url() -> str:
    """Accept a project URL or an exact Responses URL, never a browser-supplied URL."""
    endpoint = HOSTED_AGENT_RESPONSES_URL or HOSTED_AGENT_ENDPOINT
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ValueError("Configure an HTTPS HOSTED_AGENT_ENDPOINT or HOSTED_AGENT_RESPONSES_URL")
    path = parsed.path.rstrip("/")
    if not path.endswith("/responses"):
        if HOSTED_AGENT_RESPONSES_URL:
            raise ValueError("HOSTED_AGENT_RESPONSES_URL must end in /responses")
        if not HOSTED_AGENT_NAME:
            raise ValueError("HOSTED_AGENT_NAME is required")
        path += f"/agents/{quote(HOSTED_AGENT_NAME, safe='')}/endpoint/protocols/openai/responses"
    query = dict(parse_qsl(parsed.query))
    query.setdefault("api-version", HOSTED_API_VERSION)
    return urlunsplit((parsed.scheme, parsed.netloc, path, urlencode(query), ""))


def _cors_origins() -> list[str]:
    origins = []
    for value in os.getenv("CORS_ORIGINS", "").split(","):
        origin = value.strip().rstrip("/")
        if not origin:
            continue
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"https", "http"}
            or not parsed.hostname
            or "*" in origin
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("CORS_ORIGINS must contain exact HTTP(S) origins")
        origins.append(origin)
    return origins


@asynccontextmanager
async def lifespan(application: FastAPI):
    if AGENT_MODE not in SUPPORTED_MODES:
        raise ValueError("AGENT_MODE must be local, hosted, or containerapp")
    if AGENT_MODE == "hosted":
        _hosted_responses_url()
    if AGENT_MODE == "containerapp" and not CONTAINERAPP_AGENT_URL:
        raise ValueError("CONTAINERAPP_AGENT_URL is required in containerapp mode")
    timeout = float(os.getenv("HOSTED_TIMEOUT_SECONDS", "600"))
    if not 0 < timeout <= 600:
        raise ValueError("HOSTED_TIMEOUT_SECONDS must be between 0 and 600")
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=30)) as client:
        application.state.http_client = client
        if AGENT_MODE == "hosted":
            async with DefaultAzureCredential() as credential:
                application.state.token_provider = get_bearer_token_provider(
                    credential, "https://ai.azure.com/.default"
                )
                yield
        else:
            yield


app = FastAPI(title="Fibey Agent Gateway", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Session-Id"],
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    message: str = Field(min_length=1, max_length=16_000, strict=True)
    session_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: uuid.UUID


def _sse(event: str, data: dict | str) -> str:
    """Format a server-sent event."""
    payload = json.dumps(data) if isinstance(data, dict) else data
    lines = "\n".join(f"data: {line}" for line in payload.split("\n"))
    return f"event: {event}\n{lines}\n\n"


async def _run_local(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Run the agent locally and stream SSE events."""
    from fibey.agent.agent import run_agent

    session = sessions.setdefault(session_id, {})

    try:
        async for event in run_agent(message, session):
            if event["type"] == "delta":
                yield _sse("delta", {"content": event["content"]})
            elif event["type"] == "activity":
                yield _sse("activity", {
                    "tool": event.get("tool", ""),
                    "call_id": event.get("call_id", ""),
                    "status": event.get("status", ""),
                    "detail": event.get("detail", ""),
                    "args": event.get("args", ""),
                    "result": event.get("result", ""),
                    "results": event.get("results", []),
                })
            elif event["type"] == "citation":
                yield _sse("citation", {
                    "source": event.get("source", ""),
                    "url": event.get("url", ""),
                })
    except Exception as exc:
        logger.error("Local agent failed (%s)", type(exc).__name__)
        yield _sse("error", {"message": "The agent could not complete this request."})

    yield _sse("done", "[DONE]")


async def _get_hosted_token() -> str:
    """Reuse the lifespan credential and its cached, automatically refreshed token."""
    return await app.state.token_provider()


def _remember_hosted_compute_session(session_id: str, compute_id: str | None) -> None:
    if compute_id is None:
        return
    if not isinstance(compute_id, str) or not compute_id or len(compute_id) > 256:
        raise ValueError("Invalid hosted compute session identifier")
    previous = _hosted_compute_sessions.get(session_id)
    if previous is not None and previous != compute_id:
        raise ValueError("Hosted compute session changed unexpectedly")
    _hosted_compute_sessions[session_id] = compute_id


async def _read_sse(response: httpx.Response) -> AsyncGenerator[tuple[str, str], None]:
    """Read complete SSE frames, including CRLF and multiline data fields."""
    event_name = ""
    data: list[str] = []
    async for line in response.aiter_lines():
        if not line:
            if data:
                yield event_name, "\n".join(data)
            event_name, data = "", []
        elif not line.startswith(":"):
            field, separator, value = line.partition(":")
            if separator and value.startswith(" "):
                value = value[1:]
            if field == "event":
                event_name = value
            elif field == "data":
                data.append(value)


async def _run_hosted(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Translate Foundry Responses streaming into the UI's SSE contract."""
    body: dict = {"input": message, "stream": True, "store": True}
    compute_id = _hosted_compute_sessions.get(session_id)
    if compute_id:
        body["agent_session_id"] = compute_id
    previous_response_id = _hosted_sessions.get(session_id)
    if previous_response_id:
        body["previous_response_id"] = previous_response_id
    seen_call_ids: set[str] = set()
    try:
        token = await _get_hosted_token()
        async with app.state.http_client.stream(
            "POST",
            _hosted_responses_url(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            json=body,
        ) as resp:
            if resp.status_code != 200:
                logger.error("Hosted agent returned HTTP %s", resp.status_code)
                yield _sse("error", {"message": f"Hosted agent returned HTTP {resp.status_code}."})
            else:
                # Foundry creates the first sandbox; never substitute the UI's UUID.
                _remember_hosted_compute_session(session_id, resp.headers.get("x-agent-session-id"))
                terminal_received = False
                async for event_name, raw in _read_sse(resp):
                    if raw == "[DONE]":
                        break
                    event = json.loads(raw)
                    event_type = event.get("type") or event_name
                    response = event.get("response") or {}
                    _remember_hosted_compute_session(session_id, response.get("agent_session_id"))
                    if event_type == "response.completed":
                        if response.get("status", "completed") != "completed":
                            raise ValueError("Unexpected completed response status")
                        response_id = response.get("id")
                        if not isinstance(response_id, str) or not response_id:
                            raise ValueError("Completed response is missing its identifier")
                        if session_id not in _hosted_compute_sessions:
                            raise ValueError("Response is missing its hosted compute session identifier")
                        _hosted_sessions[session_id] = response_id
                        terminal_received = True
                        break
                    if event_type in {"response.failed", "response.incomplete", "response.cancelled", "error"}:
                        logger.error("Hosted agent returned a terminal failure")
                        yield _sse("error", {"message": "The hosted agent could not complete this response."})
                        terminal_received = True
                        break
                    if event_type == "response.output_text.delta":
                        if event.get("delta"):
                            yield _sse("delta", {"content": event["delta"]})
                    elif event_type == "response.output_text.annotation.added":
                        annotation = event.get("annotation", {})
                        if annotation.get("url"):
                            yield _sse("citation", {
                                "source": annotation.get("title", ""),
                                "url": annotation["url"],
                            })
                    else:
                        activity = _hosted_activity(event_type, event, seen_call_ids)
                        if activity:
                            yield _sse("activity", activity)
                if not terminal_received:
                    yield _sse("error", {"message": "The hosted agent stream ended before the response completed."})
    except httpx.TimeoutException:
        yield _sse("error", {"message": "Hosted agent request timed out"})
    except Exception as exc:
        logger.error("Hosted agent proxy failed (%s)", type(exc).__name__)
        yield _sse("error", {"message": "The hosted agent request failed."})
    yield _sse("done", "[DONE]")


def _hosted_activity(event_type: str, event: dict, seen_call_ids: set[str]) -> dict | None:
    item = event.get("item", {})
    item_type = item.get("type", "")
    call_id = item.get("call_id") or item.get("id", "")
    if event_type == "response.output_item.added":
        if item_type not in {"mcp_call", "function_call"} or call_id in seen_call_ids:
            return None
        seen_call_ids.add(call_id)
        tool = item.get("name", "tool")
        return {
            "tool": tool, "call_id": call_id, "status": "running",
            "detail": f"Calling {tool}", "args": item.get("arguments", ""), "result": "",
        }
    if event_type == "response.output_item.done":
        if item_type not in {"mcp_call", "mcp_call_output", "function_call_output"}:
            return None
        output = item.get("output") or item.get("result", "")
        error = item.get("error")
    elif event_type in {
        "response.mcp_call.completed", "response.mcp_call_completed",
        "response.mcp_call.failed", "response.mcp_call_failed",
    }:
        item = event
        call_id = event.get("call_id") or event.get("item_id", "")
        output = event.get("output") or event.get("result", "")
        error = event.get("error") or ("Tool call failed" if event_type.endswith("failed") else None)
    else:
        return None
    result = error or output
    result = result if isinstance(result, str) else json.dumps(result)
    return {
        "tool": item.get("name", ""), "call_id": call_id,
        "status": "error" if error else "complete",
        "detail": "Tool call failed" if error else "Done",
        "args": item.get("arguments", ""), "result": result[:2000],
    }


async def _run_containerapp(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Proxy to the Container App agent service and relay SSE events."""
    agent_url = CONTAINERAPP_AGENT_URL
    if not agent_url:
        yield _sse("error", {"message": "CONTAINERAPP_AGENT_URL not configured"})
        yield _sse("done", "[DONE]")
        return
    
    url = f"{agent_url.rstrip('/')}/api/chat"
    body = {"message": message, "session_id": session_id}
    
    try:
        async with app.state.http_client.stream(
            "POST", url, json=body,
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status_code != 200:
                logger.error("Agent service returned HTTP %s", resp.status_code)
                yield _sse("error", {"message": f"Agent service returned HTTP {resp.status_code}."})
            else:
                async for event_name, data in _read_sse(resp):
                    # Re-emit complete frames with their required blank delimiter.
                    yield _sse(event_name, data)
                    if event_name == "done" or data == "[DONE]":
                        return
                yield _sse("error", {"message": "The agent service stream ended before completion."})
    
    except httpx.TimeoutException:
        yield _sse("error", {"message": "Agent service request timed out"})
    except Exception as exc:
        logger.error("Container app agent proxy failed (%s)", type(exc).__name__)
        yield _sse("error", {"message": "The agent service request failed."})
    
    yield _sse("done", "[DONE]")


@app.post("/api/chat")
async def chat(body: ChatRequest):
    message, session_id = body.message, str(body.session_id)
    if AGENT_MODE not in SUPPORTED_MODES:
        raise HTTPException(status_code=503, detail="Agent mode is not configured correctly")
    if session_id in _active_sessions:
        raise HTTPException(status_code=409, detail="A request is already running in this session")
    logger.info("Gateway request: mode=%s session=%s", AGENT_MODE, session_id)
    if AGENT_MODE == "hosted":
        generator = _run_hosted(message, session_id)
    elif AGENT_MODE == "containerapp":
        generator = _run_containerapp(message, session_id)
    else:
        generator = _run_local(message, session_id)

    _active_sessions.add(session_id)

    async def stream():
        try:
            async for event in generator:
                yield event
        finally:
            try:
                await generator.aclose()
            finally:
                _active_sessions.discard(session_id)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id,
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/sessions/reset")
async def reset_session(body: ResetRequest):
    session_id = str(body.session_id)
    if session_id in _active_sessions:
        raise HTTPException(status_code=409, detail="Wait for the current response before resetting")
    sessions.pop(session_id, None)
    _hosted_sessions.pop(session_id, None)
    _hosted_compute_sessions.pop(session_id, None)
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "mode": AGENT_MODE}
