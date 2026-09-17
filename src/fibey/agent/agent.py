"""
Single agent definition with Foundry Toolbox MCP connection.

The agent calls the Toolbox as one MCP endpoint; the Toolbox dispatches
to individual tools (FoundryIQ, Work Orders OpenAPI, Inventory MCP) behind
the scenes.  When the Toolbox is configured, FoundryIQ provides knowledge
base retrieval; otherwise a local Azure AI Search function tool is used
as a fallback.
"""

import asyncio
import os
import json
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

import httpx
from azure.identity import AzureCliCredential, DefaultAzureCredential
from agent_framework import (
    Agent,
    AgentResponseUpdate,
    AgentSession,
    FileSkillsSource,
    FunctionTool,
    MCPStreamableHTTPTool,
    SkillsProvider,
)
from agent_framework.foundry import FoundryChatClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"
SKILLS_PATH = Path(__file__).parent / "skills"
_TOKEN_SCOPE = "https://ai.azure.com/.default"

# Azure AI Search configuration for direct KB queries
_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "foundry-iq-docs-index")
_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")


def _load_system_prompt() -> str:
    """Load the system prompt from markdown file."""
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return "You are Fibey, a helpful AI assistant."


def _get_credential():
    """Get Azure credential, preferring CLI for local dev."""
    try:
        cred = AzureCliCredential()
        cred.get_token(_TOKEN_SCOPE)
        return cred
    except Exception:
        cred.close()
        return DefaultAzureCredential()


def _get_token_sync(credential) -> str:
    return credential.get_token(_TOKEN_SCOPE).token


class _ToolboxAuth(httpx.Auth):
    """httpx Auth that injects a fresh bearer token for Toolbox MCP."""
    
    def __init__(self, credential):
        self._credential = credential
    
    def auth_flow(self, request):
        """Add Authorization header with a fresh token on every request."""
        request.headers["Authorization"] = f"Bearer {self._credential.get_token(_TOKEN_SCOPE).token}"
        yield request

    async def async_auth_flow(self, request):
        token = await asyncio.to_thread(_get_token_sync, self._credential)
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


class _ToolboxApiKeyAuth(httpx.Auth):
    """httpx Auth that injects the Cognitive Services account key for Toolbox MCP."""

    def __init__(self, api_key: str):
        self._api_key = api_key

    def auth_flow(self, request):
        request.headers["api-key"] = self._api_key
        yield request


def _create_toolbox_mcp(credential, resources: AsyncExitStack) -> MCPStreamableHTTPTool | None:
    """Create the Toolbox MCP tool if endpoint is configured."""
    toolbox_url = os.getenv("TOOLBOX_MCP_URL", "")
    if not toolbox_url:
        logger.warning("TOOLBOX_MCP_URL not set — running without Toolbox")
        return None

    if "api-version" not in toolbox_url:
        separator = "&" if "?" in toolbox_url else "?"
        toolbox_url = f"{toolbox_url}{separator}api-version=v1"
    
    logger.info("Toolbox MCP URL: %s", toolbox_url)

    api_key = os.getenv("TOOLBOX_API_KEY", "")
    if api_key:
        logger.info("Toolbox auth: api-key (TOOLBOX_API_KEY)")
        auth = _ToolboxApiKeyAuth(api_key)
    else:
        logger.info("Toolbox auth: Entra bearer token")
        auth = _ToolboxAuth(credential)

    auth_http_client = httpx.AsyncClient(
        auth=auth,
        headers={"Foundry-Features": "Toolboxes=V1Preview"},
        timeout=120.0,
    )
    resources.push_async_callback(auth_http_client.aclose)

    return MCPStreamableHTTPTool(
        name="toolbox",
        url=toolbox_url,
        http_client=auth_http_client,
        load_prompts=False,
    )


async def knowledge_base_search(query: str, top: int = 5) -> str:
    """Search the fiber optics field operations knowledge base.

    Searches across procedures, safety protocols, troubleshooting guides,
    equipment specs, cable types, installation standards, OTDR testing,
    and network architecture documentation.

    Args:
        query: The search query describing what you need to find.
        top: Maximum number of results to return (default 5).

    Returns:
        JSON string with search results including document name and content.
    """
    if not _SEARCH_API_KEY:
        return json.dumps({"error": "AZURE_SEARCH_API_KEY not configured"})

    search_url = f"{_SEARCH_ENDPOINT}/indexes/{_SEARCH_INDEX}/docs/search?api-version=2024-07-01"
    payload = {
        "search": query,
        "queryType": "semantic",
        "semanticConfiguration": "default",
        "top": top,
        "select": "content,metadata_storage_name",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            search_url,
            json=payload,
            headers={"api-key": _SEARCH_API_KEY, "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for doc in data.get("value", []):
        results.append({
            "source": doc.get("metadata_storage_name", "unknown"),
            "content": doc.get("content", ""),
        })

    return json.dumps({"results": results, "count": len(results)})


def _create_kb_search_tool() -> FunctionTool | None:
    """Create the knowledge base search tool if search is configured."""
    if not _SEARCH_API_KEY:
        logger.warning("AZURE_SEARCH_API_KEY not set — running without KB search")
        return None

    return FunctionTool(
        name="knowledge_base",
        description=(
            "Search the fiber optics field operations knowledge base. "
            "Covers: splicing procedures, safety protocols, OTDR testing, "
            "cable types, equipment specs, installation standards, "
            "network architecture, and troubleshooting guides."
        ),
        func=knowledge_base_search,
    )


async def _build_skills_provider(credential) -> "SkillsProvider | None":
    """Build a SkillsProvider, preferring MCP-published skills when available.

    Strategy:
      - If TOOLBOX_MCP_URL is set and SKILLS_SOURCE != "file", try to load
        skills from the toolbox MCP via resources/list + resources/read
        (SEP-2640). Falls back to FileSkillsSource on failure.
      - Otherwise use the local FileSkillsSource at SKILLS_PATH.
    """
    from .mcp_skills_source import MCPSkillsSource  # local import to avoid hard mcp dep at module load

    toolbox_url = os.getenv("TOOLBOX_MCP_URL", "")
    prefer = os.getenv("SKILLS_SOURCE", "auto").lower()  # auto | file | mcp
    if prefer not in {"auto", "file", "mcp"}:
        raise ValueError("SKILLS_SOURCE must be auto, file, or mcp")
    skill_options = {
        "disable_load_skill_approval": True,
        "disable_read_skill_resource_approval": True,
    }

    if toolbox_url and prefer in ("auto", "mcp"):
        if "api-version" not in toolbox_url:
            sep = "&" if "?" in toolbox_url else "?"
            toolbox_url = f"{toolbox_url}{sep}api-version=v1"

        api_key = os.getenv("TOOLBOX_API_KEY", "")
        auth = _ToolboxApiKeyAuth(api_key) if api_key else _ToolboxAuth(credential)
        mcp_source = MCPSkillsSource(
            url=toolbox_url,
            httpx_auth=auth,
            extra_headers={"Foundry-Features": "Toolboxes=V1Preview"},
        )
        try:
            skills = await mcp_source.get_skills()
            if skills:
                logger.info("Using MCP-published skills (%d)", len(skills))
                # Wrap loaded skills in an InMemorySkillsSource so SkillsProvider
                # doesn't re-fetch on every turn.
                from agent_framework import InMemorySkillsSource
                return SkillsProvider(InMemorySkillsSource(skills), **skill_options)
            logger.warning("MCP returned no skills; falling back to file-based skills")
        except Exception as exc:
            if prefer == "mcp":
                raise
            logger.warning("MCP skills load failed (%s); falling back to FileSkillsSource", type(exc).__name__)

    if prefer == "mcp":
        raise RuntimeError("SKILLS_SOURCE=mcp requires a toolbox URL and published skills")

    if SKILLS_PATH.is_dir():
        return SkillsProvider(FileSkillsSource(SKILLS_PATH), **skill_options)
    raise RuntimeError("Bundled Fibey skills are missing")


@asynccontextmanager
async def create_agent():
    """Own per-turn clients while the caller retains its AgentSession history."""
    async with AsyncExitStack() as resources:
        credential = await asyncio.to_thread(_get_credential)
        resources.callback(credential.close)
        client = FoundryChatClient(
            credential=credential,
            model=os.getenv("FOUNDRY_MODEL") or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        )
        resources.push_async_callback(client.project_client.close)
        resources.push_async_callback(client.client.close)
        tools = []
        toolbox_mcp = _create_toolbox_mcp(credential, resources)
        if toolbox_mcp:
            tools.append(toolbox_mcp)
        else:
            kb_tool = _create_kb_search_tool()
            if kb_tool:
                tools.append(kb_tool)
        skills_provider = await _build_skills_provider(credential)
        agent = Agent(
            client=client,
            name="fibey",
            instructions=_load_system_prompt(),
            tools=tools,
            context_providers=[skills_provider],
            default_options={"store": False},
        )
        yield agent, tools


async def run_agent(message: str, session: dict) -> AsyncGenerator[dict, None]:
    """
    Run the agent and yield streaming events.

    Events yielded:
    - {"type": "delta", "content": "..."}
    - {"type": "activity", "tool": "...", "status": "...", "detail": "..."}
    - {"type": "citation", "source": "...", "url": "..."}
    """
    import json as _json

    agent_session = session.get("agent_session")
    if not agent_session:
        agent_session = AgentSession()
        session["agent_session"] = agent_session

    async with create_agent() as (agent, tools), AsyncExitStack() as stack:
        # Initialize MCP tools
        for tool in tools:
            if isinstance(tool, MCPStreamableHTTPTool):
                await stack.enter_async_context(tool)

        stream = agent.run(
            message,
            stream=True,
            session=agent_session,
        )

        # Track tool calls to deduplicate streaming repeats and map results back
        seen_skill_loads: set[str] = set()        # dedupe repeated load_skill for same skill
        args_key_owner: dict[str, str] = {}       # name+args key → first call_id; later identical calls are suppressed
        call_id_to_name: dict[str, str] = {}
        pending_args: dict[str, str] = {}
        suppressed_call_ids: set[str] = set()     # call_ids whose events should be hidden
        emitted_running: set[str] = set()         # call_ids that already got a running event
        emitted_complete: set[str] = set()        # call_ids that already got a complete event

        async for update in stream:
            update: AgentResponseUpdate

            if update.contents:
                for content in update.contents:
                    ctype = content.type

                    if ctype == "text":
                        yield {"type": "delta", "content": content.text or ""}

                    elif ctype in ("mcp_server_tool_call", "function_call"):
                        tool_name = getattr(content, "tool_name", None) or getattr(content, "name", None) or "tool"
                        call_id = getattr(content, "call_id", None) or tool_name
                        call_id_to_name[call_id] = tool_name
                        # Accumulate arguments across streaming chunks
                        raw_args = getattr(content, "arguments", None) or ""
                        if isinstance(raw_args, dict):
                            import json as _json
                            raw_args = _json.dumps(raw_args)
                        if call_id not in pending_args:
                            pending_args[call_id] = raw_args
                            # Unwrap Foundry Toolbox tool-search-mode `call_tool` so
                            # the activity surfaces the *real* underlying tool rather
                            # than the meta-tool wrapper.
                            unwrapped_via_tool_search = False
                            if tool_name == "call_tool":
                                try:
                                    parsed = _json.loads(raw_args) if raw_args else {}
                                except Exception:
                                    parsed = {}
                                inner_name = parsed.get("name") if isinstance(parsed, dict) else None
                                if inner_name:
                                    tool_name = inner_name
                                    call_id_to_name[call_id] = inner_name
                                    inner_args = parsed.get("arguments", {}) or {}
                                    if isinstance(inner_args, (dict, list)):
                                        inner_args_str = _json.dumps(inner_args)
                                    else:
                                        inner_args_str = str(inner_args)
                                    pending_args[call_id] = inner_args_str
                                    raw_args = inner_args_str
                                    unwrapped_via_tool_search = True
                            # Detect duplicates early when args arrive in a single chunk.
                            # `args_key_owner` stores the FIRST call_id to register a given
                            # name+args key; subsequent calls with the same key are
                            # suppressed so the activity sidebar doesn't show duplicates.
                            skip = False
                            if tool_name == "load_skill":
                                try:
                                    parsed = _json.loads(raw_args) if raw_args else {}
                                    skill_key = parsed.get("skill_name", "")
                                except Exception:
                                    skill_key = ""
                                if skill_key and skill_key in seen_skill_loads:
                                    skip = True
                                    suppressed_call_ids.add(call_id)
                                elif skill_key:
                                    seen_skill_loads.add(skill_key)
                            elif raw_args:
                                try:
                                    _json.loads(raw_args)  # only dedup if args are complete JSON
                                    tool_args_key = f"{tool_name}::{raw_args}"
                                    owner = args_key_owner.get(tool_args_key)
                                    if owner is None:
                                        args_key_owner[tool_args_key] = call_id
                                    elif owner != call_id:
                                        skip = True
                                        suppressed_call_ids.add(call_id)
                                except (ValueError, TypeError):
                                    pass  # incomplete args, can't dedup yet
                            if not skip:
                                # If this is still the meta wrapper `call_tool` (because
                                # args weren't complete enough to unwrap), don't emit a
                                # placeholder yet — the safety-net unwrap at result time
                                # will emit the real tool's running event.
                                if tool_name == "call_tool" and not unwrapped_via_tool_search:
                                    pass
                                else:
                                    early_event = {
                                        "type": "activity",
                                        "tool": tool_name,
                                        "call_id": call_id,
                                        "status": "running",
                                        "detail": f"Calling {tool_name}...",
                                    }
                                    yield early_event
                                    emitted_running.add(call_id)
                        else:
                            pending_args[call_id] += raw_args

                    elif ctype in ("mcp_server_tool_result", "function_result"):
                        call_id = getattr(content, "call_id", None) or ""
                        tool_name = call_id_to_name.get(call_id) or getattr(content, "tool_name", None) or getattr(content, "name", None) or "tool"
                        import json as _json

                        # Classify failures without logging operational payloads.
                        try:
                            result_obj = getattr(content, "result", None)
                            result_repr = ""
                            is_error = False
                            if result_obj is not None:
                                if isinstance(result_obj, (dict, list)):
                                    result_repr = _json.dumps(result_obj)[:500]
                                    if isinstance(result_obj, dict):
                                        is_error = bool(result_obj.get("isError")) or "error" in result_obj
                                else:
                                    result_repr = str(result_obj)[:500]
                                    is_error = "error" in result_repr.lower()[:200]
                            logger.info(
                                "TOOL_RESULT call_id=%s tool=%s is_error=%s",
                                call_id, tool_name, is_error,
                            )
                        except Exception as log_exc:
                            logger.debug("tool-result logging failed: %s", log_exc)

                        # Safety net: if early-chunk unwrap of `call_tool` failed
                        # (args were chunked), retry now that pending_args is complete.
                        extra_meta: dict[str, Any] = {}
                        if tool_name == "call_tool":
                            try:
                                parsed_wrapper = _json.loads(pending_args.get(call_id, "") or "{}")
                            except Exception:
                                parsed_wrapper = {}
                            inner_name = parsed_wrapper.get("name") if isinstance(parsed_wrapper, dict) else None
                            if inner_name:
                                tool_name = inner_name
                                call_id_to_name[call_id] = inner_name
                                inner_args = parsed_wrapper.get("arguments", {}) or {}
                                inner_args_str = (
                                    _json.dumps(inner_args)
                                    if isinstance(inner_args, (dict, list))
                                    else str(inner_args)
                                )
                                pending_args[call_id] = inner_args_str

                        # For tool_search, parse the returned tool list and attach
                        # it to the complete event so the UI can render which tools
                        # were discovered (and later mark which ones were used).
                        if tool_name == "tool_search":
                            try:
                                raw_text = result_obj if isinstance(result_obj, str) else None
                                if raw_text is None and isinstance(result_obj, dict):
                                    content_list = result_obj.get("content") or []
                                    if content_list and isinstance(content_list, list):
                                        first = content_list[0]
                                        if isinstance(first, dict):
                                            raw_text = first.get("text")
                                if raw_text is None and result_obj is not None:
                                    raw_text = str(result_obj)
                                parsed_result = _json.loads(raw_text) if raw_text else {}
                                tools_list = parsed_result.get("tools") if isinstance(parsed_result, dict) else None
                                if isinstance(tools_list, list):
                                    extra_meta["results"] = [
                                        {
                                            "name": t.get("name", ""),
                                            "description": (t.get("description") or "").strip().split("\n")[0][:200],
                                        }
                                        for t in tools_list
                                        if isinstance(t, dict) and t.get("name")
                                    ]
                            except Exception as parse_exc:
                                logger.debug("tool_search result parse failed: %s", parse_exc)

                        # If this call was suppressed at early-chunk time
                        # (e.g., duplicate name+args), skip emitting running/complete too.
                        if call_id in suppressed_call_ids:
                            emitted_running.add(call_id)
                            emitted_complete.add(call_id)
                            continue

                        args_str = pending_args.get(call_id, "")

                        # Late dedup: if args were chunked, we couldn't detect duplicates
                        # at early-emit time. Re-check ownership with the full args now.
                        if tool_name == "load_skill":
                            try:
                                parsed = _json.loads(args_str) if args_str else {}
                                skill_name = parsed.get("skill_name", "")
                            except Exception:
                                skill_name = ""
                            if skill_name and skill_name in seen_skill_loads and call_id not in emitted_running:
                                # The skill was loaded before this call_id got an early emit.
                                suppressed_call_ids.add(call_id)
                                emitted_running.add(call_id)
                                emitted_complete.add(call_id)
                                continue
                            if skill_name and skill_name not in seen_skill_loads:
                                seen_skill_loads.add(skill_name)
                            detail = f"Loading skill: {skill_name}" if skill_name else f"Calling {tool_name}..."
                        else:
                            tool_args_key = f"{tool_name}::{args_str}"
                            owner = args_key_owner.get(tool_args_key)
                            if owner is None:
                                args_key_owner[tool_args_key] = call_id
                            elif owner != call_id and call_id not in emitted_running:
                                # An identical call already won the race; suppress this one.
                                suppressed_call_ids.add(call_id)
                                emitted_running.add(call_id)
                                emitted_complete.add(call_id)
                                continue

                            detail = f"Calling {tool_name}..."
                            try:
                                parsed = _json.loads(args_str) if args_str else {}
                                if isinstance(parsed, dict):
                                    for key in ("work_order_id", "part_id", "query"):
                                        val = parsed.get(key)
                                        if val:
                                            detail = f"Calling {tool_name} ({key}={val})"
                                            break
                            except Exception:
                                pass

                        # Emit "running" with full args if we haven't already.
                        if call_id not in emitted_running:
                            running_event = {
                                "type": "activity",
                                "tool": tool_name,
                                "call_id": call_id,
                                "status": "running",
                                "detail": detail,
                                "args": args_str,
                            }
                            running_event.update(extra_meta)
                            yield running_event
                            emitted_running.add(call_id)
                        else:
                            # We already emitted a "running" event (from the early chunk).
                            # Re-emit a running with the full args so the UI's args display
                            # gets updated to the complete value before complete fires.
                            update_event = {
                                "type": "activity",
                                "tool": tool_name,
                                "call_id": call_id,
                                "status": "running",
                                "detail": detail,
                                "args": args_str,
                            }
                            update_event.update(extra_meta)
                            yield update_event

                        # Emit the "complete" activity.
                        if call_id not in emitted_complete:
                            complete_event = {
                                "type": "activity",
                                "tool": tool_name,
                                "call_id": call_id,
                                "status": "error" if is_error else "complete",
                                "detail": f"Failed {tool_name}" if is_error else f"Completed {tool_name}",
                                "args": args_str,
                            }
                            complete_event.update(extra_meta)
                            yield complete_event
                            emitted_complete.add(call_id)

                    else:
                        # Log unknown content types for debugging
                        import logging
                        logging.getLogger(__name__).debug(
                            "Unknown content type: %s",
                            ctype,
                        )
