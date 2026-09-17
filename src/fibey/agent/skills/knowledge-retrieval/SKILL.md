---
name: knowledge-retrieval
description: Handle technical knowledge questions — procedures, safety protocols, troubleshooting, specifications, installation standards, and testing guidance. Use when the technician asks how-to questions, about procedures, safety, cable specs, OTDR testing, splicing techniques, or troubleshooting steps.
---

# Knowledge Retrieval

Use this skill when the technician asks about procedures, safety, specifications,
troubleshooting, or any technical guidance from the field operations knowledge base.

## When to Use

- "How do I perform a fusion splice?"
- "What are the safety protocols for aerial work?"
- "Troubleshoot high loss on an OTDR trace"
- "What's the bend radius for single-mode fiber?"
- "What are the installation standards for underground cable?"
- "Compare single-mode vs multi-mode fiber"

## Knowledge Base Contents

The knowledge base contains 8 reference documents:
1. **Fiber Splicing Procedures** — fusion and mechanical splice techniques, preparation, verification
2. **Safety Protocols** — PPE, aerial work, confined spaces, electrical, emergency procedures
3. **OTDR Testing Guide** — setup, trace interpretation, acceptance thresholds, troubleshooting
4. **Cable Types Reference** — single-mode, multi-mode, specs, applications, bend radius
5. **Equipment Specifications** — splicers, OTDR units, cleavers, tools, calibration
6. **Installation Standards** — underground, aerial, indoor, conduit, pull tension, routing
7. **Network Architecture** — PON, point-to-point, FTTx, distribution, topology
8. **Troubleshooting Guide** — loss, reflectance, breaks, macro-bends, connector issues

## Tools Used by This Skill

This skill calls the FoundryIQ retrieval capability exposed through the toolbox.

- Use the visible retrieval tool directly. If it is not visible and `tool_search` exists, discover it with `tool_search({"query": "knowledge base field procedures", "limit": 10})`.
- Use the exact returned name and `inputSchema`, including any nested retrieval request.
- Do not assume the old unprefixed `knowledge_base` tool exists.

## Step-by-Step Instructions

### Step 1: Search the Knowledge Base

Call the exposed retrieval tool **once**, directly or through `call_tool` only when that meta-tool exists. Preserve the user's complete question and follow the input schema; the deployed MCP tool uses a one-element `query_variants` array.

| Question Pattern | Query to Send |
|-----------------|---------------|
| How to do X | "procedure for {X}" |
| Safety for X | "safety protocols for {X}" |
| Troubleshoot X | "troubleshooting {X}" |
| Specs for X | "specifications for {X}" |
| Multi-topic | Send the full question as-is |

**CRITICAL: Always make exactly ONE knowledge base call, never multiple.**
The knowledge base searches across all documents and returns combined results.

### Step 2: Format the Response

Keep responses **concise and scannable**. Structure every response like this:

1. **Summary** (1-2 sentences max) — the key answer or takeaway up front
2. **Key steps as numbered list** — short, action-oriented bullet points (one line each).
   Keep to 5-7 steps max. Combine related steps.
3. **Collapsible sections** — put detailed info, safety notes, or full specs in
   `<details><summary>Title</summary>...</details>` blocks

**IMPORTANT formatting rules:**
- Each step should be ONE short sentence, not a paragraph
- Remove filler words — be telegraphic (e.g., "Clean fiber with 99% IPA" not "Clean the bare fiber thoroughly using isopropyl alcohol wipes until it is squeaky clean")
- Use **bold** for key terms/values only
- Combine related actions into a single step

**For procedures — lead with summary, key steps visible, details collapsed:**
```
## Fusion Splice Procedure

Strip, clean, cleave, and fuse fibers — target splice loss **≤ 0.05 dB**.

1. **Strip & clean** — Remove jacket, clean bare fiber with 99% IPA
2. **Cleave** — Cut to a clean, flat end face
3. **Fuse** — Align in splicer, run auto splice cycle
4. **Verify** — Check splice loss (target ≤ 0.05 dB)
5. **Protect** — Apply heat-shrink splice protector

<details>
<summary>⚠️ Safety Notes</summary>

- Wear safety glasses and fiber-safe gloves
- Dispose of fiber scraps in sharps container
- Never leave bare fiber on surfaces

</details>
```

**For troubleshooting — use a decision-tree pattern:**
```
## High Loss on OTDR Trace

Check in this order: dirty connectors → bad splice → macro-bend → fiber damage.

<details>
<summary>🔍 Detailed Troubleshooting Steps</summary>

1. **Dirty connectors** → Clean with one-click cleaner, re-test
2. **Bad splice** → Check splice loss at the event; re-splice if > 0.1 dB
3. **Macro-bend** → Look for tight bends (< min bend radius); re-route cable
4. **Fiber damage** → If loss persists, replace the affected segment

</details>
```

**For specifications — use a table (no collapsible needed, tables are compact):**
```
## Single-Mode Fiber (OS2)

| Spec | Value |
|------|-------|
| Core Diameter | 9 µm |
| Cladding | 125 µm |
| Wavelength | 1310/1550 nm |
| Max Attenuation | 0.35 dB/km @ 1310 nm |
| Min Bend Radius | 30 mm (loaded) |

---
**Sources**
- 📄 Cable Types Reference
```

### Step 3: Safety-First Rule

**For any topic involving safety hazards, ALWAYS lead with safety warnings before
providing the procedure or guidance.** Use the ⚠️ icon for warnings.

Topics that require safety lead-in:
- Aerial work (fall protection, bucket truck)
- Splicing (fiber shards, laser safety)
- Confined spaces (ventilation, buddy system)
- Electrical proximity (lockout/tagout)
- Chemical handling (cleaning solvents)

### Step 4: Citations

**MANDATORY:** Every response MUST end with a source citation line.

Format (always use this exact structure):
```
---
**Sources**
- 📄 Document Name 1
- 📄 Document Name 2
```

Use a horizontal rule (`---`) before the sources block to visually separate it.

Derive the document name from the knowledge base results. If uncertain, use the
closest matching document from the list in "Knowledge Base Contents" above.

**CRITICAL: Remove ALL `【...】` markers from your response.** The knowledge base may
return inline citation markers — strip them completely. Only cite sources using the
format above at the end of your response.

### Step 5: Offer Follow-Up

- If the topic relates to a job: _"Want me to pull up a work order for this job?"_
- If parts or equipment are mentioned: _"Need me to check stock on any of this equipment?"_
- If the answer is complex: _"Want me to go deeper on any of these steps?"_

## What NOT to Do

- ❌ Do not answer from your own knowledge — always search the knowledge base
- ❌ Do not skip the knowledge base search even if the same question was asked before
- ❌ Do not omit the source citation
- ❌ Do not leave `【...】` markers in your response
- ❌ Do not use inventory or work order tools for knowledge questions
- ❌ Do not skip safety warnings for hazardous procedures
