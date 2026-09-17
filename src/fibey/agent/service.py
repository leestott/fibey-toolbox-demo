"""
Legacy/local adapter wrapping the agent in a FastAPI HTTP/SSE API.

This is not deployed by the protected azure.yaml stack. Keep development
instances on loopback; the protected cloud agent runs in Foundry instead.
"""
import os
import uuid
import json
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fibey Agent Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session store (in-memory, per-replica)
# For multi-replica deployments, use Redis or sticky sessions
sessions: dict[str, dict] = {}


def _sse(event_type: str, data: any) -> str:
    """Format server-sent event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _run_agent_stream(message: str, session_id: str) -> AsyncGenerator[str, None]:
    """Run agent and stream events in SSE format."""
    from fibey.agent.agent import run_agent
    
    session = sessions.setdefault(session_id, {"history": []})
    
    try:
        async for event in run_agent(message, session):
            event_type = event.get("type", "unknown")
            
            if event_type == "delta":
                yield _sse("delta", {"content": event.get("content", "")})
            
            elif event_type == "activity":
                yield _sse("activity", {
                    "tool": event.get("tool", ""),
                    "call_id": event.get("call_id", ""),
                    "status": event.get("status", ""),
                    "detail": event.get("detail", ""),
                    "args": event.get("args", ""),
                    "result": event.get("result", ""),
                    "results": event.get("results", []),
                })
            
            elif event_type == "citation":
                yield _sse("citation", {
                    "source": event.get("source", ""),
                    "url": event.get("url", ""),
                })
            
            elif event_type == "error":
                yield _sse("error", {"message": event.get("message", "Unknown error")})
    
    except Exception as exc:
        logger.error("Agent error (%s)", type(exc).__name__)
        yield _sse("error", {"message": "The agent could not complete this request."})
    
    yield _sse("done", "[DONE]")


@app.post("/api/chat")
async def chat(request: Request):
    """
    Chat endpoint compatible with the gateway's expected interface.
    
    Request body:
        {
            "message": "user message",
            "session_id": "optional-session-id"
        }
    
    Response: Server-sent events stream with delta, activity, citation, error, and done events.
    """
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", str(uuid.uuid4()))
    
    return StreamingResponse(
        _run_agent_stream(message, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": session_id,
        },
    )


@app.post("/api/sessions/reset")
async def reset_session(request: Request):
    """Reset/clear a session's history."""
    body = await request.json()
    session_id = body.get("session_id", "")
    sessions.pop(session_id, None)
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "containerapp"}
