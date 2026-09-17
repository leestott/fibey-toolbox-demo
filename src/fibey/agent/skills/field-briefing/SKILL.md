---
name: field-briefing
description: Provide a comprehensive field briefing for a work order — combining work order details, parts availability, and relevant technical procedures or safety protocols from the knowledge base. Use when the technician wants a full briefing, walkthrough, or complete preparation guide for a job.
---

# Field Briefing

Use this skill to give the technician a complete briefing before heading to a job site.
This combines work order details, parts availability, and relevant procedures/safety info.

## When to Use

- "Brief me on WO-007"
- "Give me the full rundown for WO-003"
- "Walk me through what I need for my next job"
- "Full briefing for WO-010"
- "What should I know before heading to the splice job?"

## Tools Used by This Skill

This skill uses **three** capabilities from the Foundry Toolbox in sequence:

| # | Capability | Prefixed tool name |
|---|---|---|
| 1 | Get the work order | Discover the `get_work_order` operation |
| 2 | Check stock for the parts list | `inventory___check_stock_batch` |
| 3 | Search procedures & safety | Discover the FoundryIQ retrieval tool |

### Step 0: Discover tools (REQUIRED before first call this turn)

If any of these tools isn't already visible in your tool list, run **one** combined `tool_search` with **`limit: 10`**:

```
tool_search({"query": "work order parts stock knowledge base", "limit": 10})
```

**Never** run one search per capability — a single combined query with `limit: 10` returns all needed tools, and they stay callable for the rest of the turn.

## Step-by-Step Instructions

### Step 1: Fetch the Work Order

Call the exposed work-order lookup directly, or through `call_tool` only if that meta-tool exists, using its schema and the requested work-order ID.
Note the job type from the title and description — you'll need this to search
the knowledge base for relevant procedures.

### Step 2: Check Parts Availability

Call the exposed batch-stock tool with `{"part_ids": [<all part_ids>]}` in a single call, using the available direct or meta-tool interface.
Do NOT call `check_stock` individually for each part.
Classify each as ✅ Ready, ⚠️ Partial, or ❌ Unavailable.

### Step 3: Search the Knowledge Base

Call the exposed FoundryIQ retrieval tool using its returned input schema and the available direct or meta-tool interface.

Based on the work order's job type, search for relevant procedures **and** safety protocols.

**IMPORTANT: Make one knowledge retrieval call** with a combined query that covers both the procedure and safety info. For example:
_"fusion splice procedure and safety protocols for aerial fiber work"_

Do NOT make separate calls for procedures and safety — combine them into a single query. This is more efficient and avoids redundant lookups.

### Step 4: Present the Complete Briefing

Structure the response in this order. Use collapsible `<details>` sections
for safety notes and full procedures to keep the briefing scannable.
The job details table and parts checklist should always be visible.

```
## Field Briefing — WO-007: Fiber Splice Repair

### 📋 Job Details

| Field | Value |
|-------|-------|
| **Status** | 🟡 In Progress |
| **Priority** | 🔴 Critical |
| **Technician** | Mike Chen |
| **Location** | 456 Industrial Pkwy, Building C |
| **Due Date** | 2025-06-15 |

**Description:** Repair damaged fiber splice in distribution panel, Building C, 3rd floor.

---

### 🔧 Parts Checklist

| Part ID | Part Name | Need | Available | Status |
|---------|-----------|------|-----------|--------|
| FIB-012 | SC Connector | 2 | 342 | ✅ Ready |
| FIB-045 | Splice Tray | 1 | 0 | ❌ Unavailable |

**Parts Status:** ⚠️ 1 of 2 parts unavailable

---

<details>
<summary>⚠️ Safety Notes</summary>

- Wear safety glasses and fiber-safe gloves
- Use a sharps container for fiber scraps
- [Any other relevant safety protocols from KB]

</details>

<details>
<summary>📖 Procedure Reference</summary>

1. Strip the fiber jacket
2. Clean with IPA wipes
3. Cleave to flat end face
4. Align in fusion splicer
5. Run splice cycle
6. Verify loss ≤ 0.05 dB
7. Apply heat-shrink protector

</details>
```

### Step 5: Closing Summary

End with a quick go/no-go assessment:
- ✅ All clear: _"You're all set — parts are available and you have the procedure. Good luck out there!"_
- ⚠️ Partial: _"Heads up: some parts are unavailable. You may want to resolve that before heading out."_
- ❌ Blocked: _"Hold off — critical parts are missing. Want me to help find alternatives?"_

## Delegation Rules

This skill uses **all three tool types** in sequence:
1. **Work orders API** → get WO details and job type
2. **Inventory tools** → check stock for parts_needed
3. **Knowledge base** → pull procedure and safety info based on job type

## Citation Rules

- ALWAYS end with the sources block listing all KB documents referenced, using this format:
```
---
**Sources**
- 📄 Document Name 1
- 📄 Document Name 2
```
- Remove all `【...】` markers from the response
- Derive document names from the knowledge base results

## What NOT to Do

- ❌ Do not skip any section (job details, safety, parts, procedure)
- ❌ Do not skip safety — always include safety notes for the job type
- ❌ Do not answer procedure questions from your own knowledge — use the KB
- ❌ Do not guess part availability — check each one
- ❌ Do not omit source citations
