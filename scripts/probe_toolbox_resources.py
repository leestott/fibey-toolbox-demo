"""Probe MCP resources from the Foundry Toolbox endpoint."""
import asyncio
import os
import sys
import contextlib

import httpx
from azure.identity import AzureCliCredential
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "https://ai-fibey.services.ai.azure.com/api/projects/fibey-project-westus2/toolboxes/fibey-toolbox-linda/mcp?api-version=v1"
SCOPE = "https://ai.azure.com/.default"


async def main():
    cred = AzureCliCredential()
    token = cred.get_token(SCOPE).token
    headers = {
        "Authorization": f"Bearer {token}",
        "Foundry-Features": "Toolboxes=V1Preview",
    }

    async with streamablehttp_client(URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("Server:", init.serverInfo.name if init.serverInfo else "?")
            print("Capabilities:", init.capabilities)

            print("\n--- resources/list ---")
            try:
                r = await session.list_resources()
                for res in r.resources:
                    print(f"  {res.uri}  name={res.name!r}  desc={res.description!r}  mime={res.mimeType!r}")
                if r.resources:
                    print("\n--- resources/read (first one) ---")
                    first = r.resources[0]
                    read_result = await session.read_resource(first.uri)
                    for content in read_result.contents:
                        text = getattr(content, "text", None)
                        if text:
                            print(f"URI: {content.uri}")
                            print(f"MIME: {getattr(content, 'mimeType', '?')}")
                            print(f"Content (first 500 chars):\n{text[:500]}")
                            print(f"... [{len(text)} chars total]")
            except Exception as e:
                print("resources/list failed:", type(e).__name__, e)

            print("\n--- resources/templates/list ---")
            try:
                t = await session.list_resource_templates()
                for tmpl in t.resourceTemplates:
                    print(f"  {tmpl.uriTemplate}  name={tmpl.name!r}")
            except Exception as e:
                print("templates list failed:", type(e).__name__, e)


asyncio.run(main())
