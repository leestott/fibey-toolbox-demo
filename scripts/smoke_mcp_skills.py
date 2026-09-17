"""Smoke test for MCPSkillsSource against the Foundry Toolbox."""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
import httpx
from azure.identity import AzureCliCredential

load_dotenv()
logging.basicConfig(level=logging.INFO)

from fibey.agent.agent import _ToolboxAuth, _ToolboxApiKeyAuth  # noqa: E402
from fibey.agent.mcp_skills_source import MCPSkillsSource  # noqa: E402


async def main():
    url = os.environ["TOOLBOX_MCP_URL"]
    if "api-version" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}api-version=v1"

    api_key = os.getenv("TOOLBOX_API_KEY", "")
    auth = _ToolboxApiKeyAuth(api_key) if api_key else _ToolboxAuth(AzureCliCredential())
    source = MCPSkillsSource(
        url=url,
        httpx_auth=auth,
        extra_headers={"Foundry-Features": "Toolboxes=V1Preview"},
    )
    skills = await source.get_skills()
    print(f"\nLoaded {len(skills)} skill(s):")
    for s in skills:
        print(f"  - {s.frontmatter.name}: {s.frontmatter.description[:90]}...")
        print(f"      instructions len: {len(s.instructions)}")


asyncio.run(main())
