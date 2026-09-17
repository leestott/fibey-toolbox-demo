from __future__ import annotations

import json
import hmac
import logging
import os
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

DATA_PATH = Path(__file__).parent / "data" / "inventory.json"
INVENTORY: list[dict[str, Any]] = json.loads(DATA_PATH.read_text())
PARTS_BY_ID = {part["id"]: part for part in INVENTORY}

server = FastMCP(
    name="fiber-inventory",
    instructions="Manage and query fiber optics parts inventory.",
    host="0.0.0.0",
    port=8001,
    stateless_http=True,
)


class ApiKeyMiddleware:
    def __init__(self, app):
        self.app = app
        self.key = os.getenv("API_KEY", "")
        if os.getenv("REQUIRE_API_KEY", "false").lower() == "true" and len(self.key) < 32:
            raise RuntimeError("API_KEY must contain at least 32 characters")
        if not self.key:
            logging.getLogger(__name__).warning("Inventory authentication disabled for local development")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] != "/health" and self.key:
            request = Request(scope)
            supplied = request.headers.get("x-api-key", "")
            if not hmac.compare_digest(supplied.encode(), self.key.encode()):
                await JSONResponse({"detail": "Unauthorized"}, status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


class DashboardText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


@server.tool(description="Read the synthetic FiberNet status dashboard: outages, network segments, OLT status and incidents.")
async def get_network_status() -> dict[str, str]:
    url = os.getenv("STATUS_DASHBOARD_URL", "")
    if not url:
        raise RuntimeError("STATUS_DASHBOARD_URL is not configured")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url)
        response.raise_for_status()
    parser = DashboardText()
    parser.feed(response.text)
    return {"source": "FiberNet synthetic demo dashboard", "content": "\n".join(parser.parts)}


def _stock_status(part: dict[str, Any]) -> str:
    quantity = int(part["stock_quantity"])
    threshold = int(part["min_stock_threshold"])
    if quantity <= 0:
        return "out-of-stock"
    if quantity <= threshold:
        return "low"
    return "in-stock"


def _get_part_or_raise(part_id: str) -> dict[str, Any]:
    part = PARTS_BY_ID.get(part_id.upper())
    if part is None:
        raise ValueError(f"Unknown part_id: {part_id}")
    return part


def _part_summary(part: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": part["id"],
        "name": part["name"],
        "category": part["category"],
        "sku": part["sku"],
        "unit_price": part["unit_price"],
        "stock_quantity": part["stock_quantity"],
        "stock_status": _stock_status(part),
        "location": part["location"],
        "manufacturer": part["manufacturer"],
    }


@server.tool(
    description="List all fiber optic inventory parts, optionally filtered by category.",
)
def list_parts(category: str | None = None) -> dict[str, Any]:
    """Return part summaries for the full catalog or a single category."""
    normalized_category = category.strip().lower() if category else None
    parts = [
        _part_summary(part)
        for part in INVENTORY
        if normalized_category is None or part["category"].lower() == normalized_category
    ]
    return {
        "count": len(parts),
        "category": category,
        "parts": parts,
    }


@server.tool(
    description="Search fiber optic parts by name or description using a free-text query.",
)
def search_parts(query: str) -> dict[str, Any]:
    """Return matching part summaries for a case-insensitive search query."""
    normalized_query = query.strip().lower()
    if not normalized_query:
        raise ValueError("query must not be empty")

    matches = [
        _part_summary(part)
        for part in INVENTORY
        if normalized_query in part["name"].lower()
        or normalized_query in part["description"].lower()
    ]
    return {
        "query": query,
        "count": len(matches),
        "parts": matches,
    }


@server.tool(
    description="Get the full inventory record for a part by its part ID.",
)
def get_part_details(part_id: str) -> dict[str, Any]:
    """Return the full part record, including pricing, stock, and warehouse details."""
    part = dict(_get_part_or_raise(part_id))
    part["stock_status"] = _stock_status(part)
    return part


@server.tool(
    description="Check the current stock level and status for a part.",
)
def check_stock(part_id: str) -> dict[str, Any]:
    """Return stock quantity, reorder threshold, and inventory status for a part."""
    part = _get_part_or_raise(part_id)
    return {
        "id": part["id"],
        "name": part["name"],
        "stock_quantity": part["stock_quantity"],
        "min_stock_threshold": part["min_stock_threshold"],
        "stock_status": _stock_status(part),
        "location": part["location"],
    }


@server.tool(
    description="Check stock levels for multiple parts at once. Use this instead of repeated check_stock calls when you need to verify availability for a list of parts (e.g. all parts on a work order).",
)
def check_stock_batch(part_ids: list[str]) -> dict[str, Any]:
    """Return stock status for each requested part and a summary."""
    results: list[dict[str, Any]] = []
    counts = {"in_stock": 0, "low": 0, "out_of_stock": 0, "not_found": 0}

    for pid in part_ids:
        try:
            part = _get_part_or_raise(pid)
            status = _stock_status(part)
            results.append({
                "id": part["id"],
                "name": part["name"],
                "stock_quantity": part["stock_quantity"],
                "min_stock_threshold": part["min_stock_threshold"],
                "stock_status": status,
                "location": part["location"],
            })
            if status == "in-stock":
                counts["in_stock"] += 1
            elif status == "low":
                counts["low"] += 1
            else:
                counts["out_of_stock"] += 1
        except ValueError:
            results.append({"id": pid.upper(), "error": f"Unknown part_id: {pid}"})
            counts["not_found"] += 1

    return {
        "results": results,
        "summary": {
            "total": len(part_ids),
            **counts,
        },
    }


@server.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(_: Request) -> Response:
    return JSONResponse(
        {
            "status": "ok",
            "service": "inventory-mcp",
            "parts_loaded": len(INVENTORY),
        }
    )


app = server.streamable_http_app()
app.add_middleware(ApiKeyMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
