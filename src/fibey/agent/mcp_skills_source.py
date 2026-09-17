"""SkillsSource that loads skills from an MCP server's resources/list + resources/read.

This adapter lets the Microsoft Agent Framework's existing Skills orchestration
(SkillsProvider) consume skills published as MCP resources by a Foundry Toolbox
(SEP-2640 skills extension), without modifying the framework.

Resources are expected at URIs like `skill://{name}/SKILL.md` with text/markdown
content containing YAML frontmatter (name + description) followed by markdown
instructions. Supporting files (resource templates) are not loaded — only the
top-level SKILL.md per skill is materialized as an InlineSkill.
"""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

import httpx
import yaml
from agent_framework import (
    InlineSkill,
    Skill,
    SkillFrontmatter,
    SkillsSource,
)
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


def _parse_skill_markdown(text: str) -> tuple[dict, str]:
    """Parse a SKILL.md body into (frontmatter_dict, instructions_body).

    Tolerates multiple `---`-delimited YAML blocks at the top, possibly
    separated by blank lines (Foundry Toolbox currently emits an empty
    stub block before the real one). Non-empty fields from later blocks
    override earlier ones.
    """
    lines = text.lstrip("\ufeff").splitlines()
    last_fm: dict = {}
    body_start = 0
    i = 0
    while i < len(lines):
        # Skip blank lines between (or before) frontmatter blocks.
        while i < len(lines) and lines[i].strip() == "":
            i += 1
        if i >= len(lines) or lines[i].strip() != "---":
            break
        # Find closing ---.
        j = i + 1
        while j < len(lines) and lines[j].strip() != "---":
            j += 1
        if j >= len(lines):
            break
        block = "\n".join(lines[i + 1 : j])
        try:
            parsed = yaml.safe_load(block) or {}
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    if v not in (None, ""):
                        last_fm[k] = v
        except yaml.YAMLError as exc:
            logger.warning("Failed to parse frontmatter block: %s", exc)
        i = j + 1
        body_start = i
    body = "\n".join(lines[body_start:]).lstrip("\n")
    return last_fm, body


class MCPSkillsSource(SkillsSource):
    """Loads skills from an MCP server that publishes SKILL.md as resources.

    The source opens a one-shot ClientSession against the configured MCP
    endpoint, calls `resources/list`, fetches each `skill://*/SKILL.md`
    resource via `resources/read`, parses the frontmatter, and returns
    `InlineSkill` instances suitable for SkillsProvider.

    Auth is delegated to the provided `httpx_auth` (any `httpx.Auth`) and
    `extra_headers` (e.g. `Foundry-Features: Toolboxes=V1Preview`).
    """

    def __init__(
        self,
        *,
        url: str,
        httpx_auth: httpx.Auth | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._url = url
        self._auth = httpx_auth
        self._extra_headers = dict(extra_headers or {})
        self._timeout = timeout

    def _build_request_headers(self) -> dict[str, str]:
        """Build the static headers for the MCP transport.

        The streamable_http client only accepts a static dict, so we resolve
        the auth flow once to capture the auth header. We deliberately
        whitelist auth-only headers (Authorization / api-key) to avoid
        leaking body-related headers (Content-Length, Content-Type, Host).
        """
        headers = dict(self._extra_headers)
        if self._auth is not None:
            dummy = httpx.Request("POST", self._url)
            flow = self._auth.auth_flow(dummy)
            try:
                req = next(flow)
                for name in ("authorization", "api-key"):
                    val = req.headers.get(name)
                    if val:
                        headers[name.title() if name == "authorization" else name] = val
            except StopIteration:
                pass
            finally:
                flow.close()
        return headers

    async def get_skills(self) -> list[Skill]:
        headers = self._build_request_headers()
        skills: list[Skill] = []
        try:
            async with streamablehttp_client(self._url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listing = await session.list_resources()
                    for res in listing.resources:
                        uri_str = str(res.uri)
                        if not uri_str.startswith("skill://") or not uri_str.endswith("/SKILL.md"):
                            continue
                        try:
                            content_resp = await session.read_resource(res.uri)
                        except Exception as exc:
                            logger.warning("Failed to read MCP skill resource %s: %s", uri_str, exc)
                            continue

                        text = next(
                            (
                                getattr(c, "text", None)
                                for c in content_resp.contents
                                if getattr(c, "text", None)
                            ),
                            None,
                        )
                        if not text:
                            logger.warning("MCP skill resource %s has no text content; skipping", uri_str)
                            continue

                        fm, body = _parse_skill_markdown(text)
                        name = fm.get("name") or res.name
                        description = fm.get("description") or res.description or ""
                        if not name or not description:
                            logger.warning(
                                "Skipping MCP skill %s: missing name or description after parse", uri_str
                            )
                            continue
                        try:
                            frontmatter = SkillFrontmatter(name=name, description=description)
                        except ValueError as exc:
                            logger.warning("Invalid frontmatter for %s: %s", uri_str, exc)
                            continue
                        skills.append(InlineSkill(frontmatter=frontmatter, instructions=body))
                        logger.info("Loaded MCP skill: %s", name)
        except Exception as exc:
            logger.error("Failed to load skills from MCP %s: %s", self._url, exc)
            raise

        logger.info("MCPSkillsSource loaded %d skill(s) from %s", len(skills), self._url)
        return skills
