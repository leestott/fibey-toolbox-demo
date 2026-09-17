---
name: "Agent Developer"
description: "Microsoft Agent Framework + Foundry Toolbox MCP integration specialist"
tags: ['python', 'azure', 'agent-framework', 'mcp', 'foundry']
---

# Agent Developer Skill

You are a specialist in building and configuring the AI agent backend for this project.

## Tech Stack
- Python 3.11+
- Microsoft Agent Framework 1.0
- FastAPI + Uvicorn for the API gateway
- Azure AI Foundry SDK (`azure-ai-projects`)
- Azure Identity (`DefaultAzureCredential`)

## Architecture

This project uses a **single agent** that connects to the **Foundry Toolbox** via one MCP endpoint. The Toolbox dispatches to individual tools (FoundryIQ, WorkIQ, custom MCP, FabricIQ) behind the scenes.

```
API Gateway → Single Agent → Toolbox (MCP endpoint) → Multiple Tools
```

### Agent Modes
- **Local** (`AGENT_MODE=local`): Agent runs in-process, connects to Toolbox MCP directly via `MCPStdioTool` or `MCPStreamableHTTPTool`
- **Hosted** (`AGENT_MODE=hosted`): Agent deployed as container in Foundry Agent Service, Toolbox configured via Foundry project

## Streaming Protocol
The gateway streams newline-delimited JSON events:
```json
{"type": "message", "content": "chunk of text"}
{"type": "activity", "tool": "FoundryIQ", "status": "running", "detail": "Searching knowledge base..."}
{"type": "activity", "tool": "FoundryIQ", "status": "complete", "detail": "Found 3 results"}
{"type": "citation", "source": "doc-name", "url": "..."}
```

Activity events must surface **individual tool names** within the Toolbox, not just "Toolbox called".

## File Organization
```
src/fibey/agent/
├── api_server.py     # FastAPI gateway
├── main.py           # Local-mode entrypoint
├── hosted.py         # Hosted-mode entrypoint
├── agent.py          # Agent definition + Toolbox MCP connection
└── prompts/
    └── system_prompt.md
```

## Conventions
- System prompts are stored as markdown in `prompts/` and loaded at runtime
- Use `python-dotenv` for environment configuration
- All Azure auth via `DefaultAzureCredential`
- Type hints on all function signatures
- Use `asyncio` and `async/await` throughout — the agent framework is async-first
