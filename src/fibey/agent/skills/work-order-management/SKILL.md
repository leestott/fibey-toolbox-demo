---
name: work-order-management
description: Handle work order operations — viewing, listing, creating, and updating work orders. Use when the technician asks about work orders, assignments, scheduling, job status, or needs to create or update a WO.
---

# Work Order Management

Use this skill for any work order operation — viewing, listing, creating, or updating.

## When to Use

- "Show me WO-007"
- "What are my open work orders?"
- "Create a work order for fiber splice at 123 Main St"
- "Mark WO-003 as completed"
- "What critical work orders are pending?"
- "Assign WO-010 to Sarah"

## Tools Used by This Skill

Work-order capabilities are generated from the protected OpenAPI definition in the Foundry Toolbox. Discover their exact names and input schemas before calling them.

| Capability | Prefixed tool name |
|---|---|
| List / filter work orders | Discover `list_work_orders` |
| Get a specific work order | Discover `get_work_order` |
| Create a work order | Discover `create_work_order` |
| Update a work order | Discover `update_work_order` |

### Step 0: Discover tools (REQUIRED before first work-order call this turn)

If the work-order tools aren't already visible in your tool list, call `tool_search` **once** with **`limit: 10`** and a short query like `"work order"`. Examples:

- `tool_search({"query": "work order", "limit": 10})`
- `tool_search({"query": "create work order", "limit": 10})` for create flows

The returned tools stay callable for the rest of the turn — do not search again.

### Step 1: Choose the Right Operation

| Request Type | Tool (prefixed name) | Key Parameters |
|-------------|--------------|----------------|
| View a specific WO | Discovered lookup | `work_order_id` (e.g. `WO-007`) |
| List / filter WOs | Discovered list | `status`, `priority`, `assigned_technician` |
| Create a new WO | Discovered create | title, description, priority, technician, location, due_date |
| Update an existing WO | Discovered update | `work_order_id` + fields to change |

Call visible operational tools directly; use `call_tool` only if that meta-tool is available. Follow the returned schema, including the `body` wrapper for create and update.

**Always use filters when listing.** If the technician asks "what are my open work orders?",
filter by `status=open` rather than listing all and filtering yourself.

### Step 2: Format the Response

**For a single work order:**
```
## WO-007 — Fiber Splice Repair

| Field | Value |
|-------|-------|
| **Status** | 🟡 In Progress |
| **Priority** | 🔴 Critical |
| **Technician** | Mike Chen |
| **Location** | 456 Industrial Pkwy, Building C |
| **Due Date** | 2025-06-15 |
| **Parts Needed** | FIB-012 (×2), FIB-045 (×1) |

**Description:** Repair damaged fiber splice in distribution panel, Building C, 3rd floor.
```

**For multiple work orders, use a summary table:**

| WO ID | Title | Status | Priority | Technician | Due Date |
|-------|-------|--------|----------|------------|----------|
| WO-003 | Cable Install | 🟢 Open | 🟡 Medium | Sarah Kim | 2025-06-10 |
| WO-007 | Splice Repair | 🟡 In Progress | 🔴 Critical | Mike Chen | 2025-06-15 |

### Step 3: Status & Priority Indicators

**Always include the label text after the icon** — never show a bare colored circle.

**Status:**
- 🟢 Open — not yet started
- 🟡 In Progress — work underway
- ✅ Completed — finished
- ⛔ Cancelled — cancelled

**Priority:**
- 🔴 Critical — immediate attention
- 🟠 High — urgent
- 🟡 Medium — standard
- 🟢 Low — when time allows

When status and priority appear on the same line (e.g., in a header), use labels to disambiguate:
`🟡 In Progress | 🟡 Medium Priority` — not `🟡 | 🟡`

### Step 4: Handle Creates and Updates

**On create:** Confirm with the technician before submitting if any required field is missing.
Required: title, description, priority, assigned_technician, location, due_date.

**On update:** After a successful update, echo back exactly what changed:
```
✅ **WO-007 updated:**
- Status: In Progress → **Completed**
- Updated at: 2025-06-15T14:30:00Z
```

### Step 5: Cross-Reference Parts

If a work order has `parts_needed`, mention them by part ID so the technician can follow up 
with an inventory check. Offer: _"Want me to check stock on these parts?"_

## What NOT to Do

- ❌ Do not invent work order IDs or details
- ❌ Do not list all work orders without applying filters when the user specifies criteria
- ❌ Do not create a work order without confirming missing required fields
- ❌ Do not use knowledge base tools for work order questions
- ❌ Do not guess the status or priority — read it from the response
