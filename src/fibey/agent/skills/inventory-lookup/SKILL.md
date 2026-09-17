---
name: inventory-lookup
description: Handle inventory, parts, and network status queries — stock checks, part lookups, availability, equipment searches, outages, and dashboard incidents.
---

# Inventory Lookup

Use this skill when the technician asks about parts, stock, equipment, or availability.

## When to Use

- "Do we have any SC connectors?"
- "What's the stock on FIB-042?"
- "Show me all splice equipment"
- "Is the OTDR available?"
- "What connectors do we carry?"
- "Check stock for the parts on WO-007"

## Tools Used by This Skill

All inventory capabilities live in the Foundry Toolbox under the `inventory` MCP server, so the actual tool names are prefixed `inventory___`.

| Capability | Prefixed tool name |
|---|---|
| Free-text part search | `inventory___search_parts` |
| Browse / filter list | `inventory___list_parts` |
| Single-part details | `inventory___get_part_details` |
| Single-part stock | `inventory___check_stock` |
| Multi-part stock | `inventory___check_stock_batch` |
| Read the synthetic network dashboard | `inventory___get_network_status` |

### Network status

For outages, incidents or network status, discover the dashboard retrieval tool,
then call the returned tool with its declared schema. It takes no user-supplied
URL and only reads the configured internal dashboard. Summarize relevant
incidents and explicitly label the result as synthetic demo status; do not run
inventory lookups unless the request also asks about parts.

### Step 0: Discover tools (REQUIRED before first inventory call this turn)

If the inventory tools aren't already visible in your tool list, call `tool_search` **once** with **`limit: 10`**. Use a query made from the technician's own domain terms — the toolbox is indexed with fiber-tech vocabulary so terms like `"OTDR"`, `"splicer"`, `"VFL"`, `"connector"`, `"patch cord"`, `"splice tray"`, `"test equipment"` all match inventory tools directly.

Examples:
- "OTDR stock?" → `tool_search({"query": "OTDR", "limit": 10})`
- "do we have SC connectors?" → `tool_search({"query": "SC connector", "limit": 10})`
- generic "check parts" → `tool_search({"query": "inventory parts stock", "limit": 10})`

Always pass `limit: 10` so all inventory tools surface. The returned tools stay callable for the rest of the turn — do not call `tool_search` again for inventory in this turn.

If `tool_search` returns no matching tools, refine the query once. If discovery still fails, report that the capability is unavailable; never assume an undiscovered tool exists.

### Step 1: Choose the Right Tool

| Question Type | Tool (prefixed name) | Example |
|--------------|-------------|---------|
| Free-text search ("do we have…", "find…") | `inventory___search_parts` | "do we have splice trays?" |
| Browse by category | `inventory___list_parts` with `category` filter | "show all connectors" |
| Specific part by ID | `inventory___get_part_details` with `part_id` | "details on FIB-012" |
| Stock level for a known part | `inventory___check_stock` with `part_id` | "how many FIB-042 in stock?" |
| Stock levels for multiple parts | `inventory___check_stock_batch` with `part_ids` list | "check stock for FIB-003 and FIB-012" |

Call visible operational tools directly. Use `call_tool` only when the toolbox actually exposes that meta-tool, with the exact discovered name and arguments.

**Categories available:** Connectors, Cables, Splitters, Splice Equipment, Test Equipment

### Step 2: Format the Response

**For a single part:**
```
**FIB-042 — SC/APC Connector** 🟢 In Stock
- **SKU:** CONN-SC-APC-500
- **Stock:** 342 units (Warehouse A)
- **Price:** $4.50/unit
- **Manufacturer:** Corning
```

**For multiple parts (2+), ALWAYS use a table with status indicators:**

```
### Inventory Results

| Part | Stock | Status | Location |
|------|-------|--------|----------|
| SC Connector (FIB-012) | 342 | 🟢 In Stock | WH-A1 |
| LC Connector (FIB-015) | 12 | 🟡 Low Stock | WH-B2 |
| Splice Tray (FIB-023) | 0 | 🔴 Out of Stock | — |

> 🟡 **Note:** LC Connectors are running low — consider reordering.
```

**CRITICAL:** When checking multiple items, always use a markdown table. Never
list items as a plain paragraph. Separate different topics with `---` dividers
or `###` headers.

### Step 3: Interpret Stock Status

Always show a status indicator:
- 🟢 **In Stock** — quantity is above minimum threshold
- 🟡 **Low Stock** — quantity is at or below minimum threshold but > 0. Add: _"Stock is running low — consider reordering."_
- 🔴 **Out of Stock** — quantity is 0. Add: _"Currently unavailable. Check with supply chain for restock ETA."_

### Step 4: Provide Actionable Next Steps

- If stock is low or out: suggest reordering or checking alternatives
- If the technician seems to be prepping for a job: offer to check a work order's full parts list
- If they searched broadly: ask if they need details on a specific part

## What NOT to Do

- ❌ Do not guess stock quantities — always use the inventory tools
- ❌ Do not skip the stock status indicator
- ❌ Do not use knowledge base tools for inventory questions
- ❌ Do not invent part IDs or SKUs
- ❌ Do not list multiple items as a flat paragraph — always use tables
