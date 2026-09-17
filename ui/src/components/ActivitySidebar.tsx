import { useState, useRef, useCallback } from "react";
import type { ActivityEvent } from "../api/client";

interface ActivitySidebarProps {
  activities: ActivityEvent[];
  isStreaming: boolean;
  onClear?: () => void;
}

/** Map raw tool names to friendly display names and icons */
function parseToolInfo(raw: string): { name: string; icon: string; category: string; source: string } {
  const lower = raw.toLowerCase();

  // Skill loading
  if (lower === "load_skill" || lower.includes("load_skill")) {
    return { name: "Load Skill", icon: "psychology", category: "skill", source: "Agent Framework" };
  }

  // Foundry Toolbox tool-search meta-tools
  if (lower === "tool_search") {
    return { name: "Tool Search", icon: "travel_explore", category: "discovery", source: "Foundry Toolbox" };
  }
  if (lower === "call_tool") {
    // Fallback when gateway did not unwrap (incomplete args at result time).
    return { name: "Call Tool", icon: "play_arrow", category: "discovery", source: "Foundry Toolbox" };
  }

  // Knowledge base
  if (lower === "knowledge_base" || lower.includes("knowledge_base")) {
    return { name: "Knowledge Base", icon: "menu_book", category: "knowledge", source: "FoundryIQ" };
  }

  // Work orders — match verbose Toolbox MCP names
  if (lower.includes("work_order")) {
    if (lower.includes("list") || lower.includes("get_work_orders"))
      return { name: "List Work Orders", icon: "list_alt", category: "work-orders", source: "Work Orders API" };
    if (lower.includes("create") || lower.includes("post"))
      return { name: "Create Work Order", icon: "add_task", category: "work-orders", source: "Work Orders API" };
    if (lower.includes("update") || lower.includes("put") || lower.includes("patch"))
      return { name: "Update Work Order", icon: "edit_note", category: "work-orders", source: "Work Orders API" };
    return { name: "Get Work Order", icon: "assignment", category: "work-orders", source: "Work Orders API" };
  }

  // Inventory — match verbose Toolbox MCP names
  if (lower.includes("inventory") || lower.includes("check_stock") || lower.includes("search_parts") || lower.includes("get_part") || lower.includes("list_parts")) {
    if (lower.includes("check_stock_batch"))
      return { name: "Check Stock (Batch)", icon: "inventory_2", category: "inventory", source: "Inventory MCP" };
    if (lower.includes("check_stock"))
      return { name: "Check Stock", icon: "inventory_2", category: "inventory", source: "Inventory MCP" };
    if (lower.includes("search"))
      return { name: "Search Parts", icon: "search", category: "inventory", source: "Inventory MCP" };
    if (lower.includes("list"))
      return { name: "List Parts", icon: "format_list_bulleted", category: "inventory", source: "Inventory MCP" };
    if (lower.includes("get_part_details") || lower.includes("get_part"))
      return { name: "Part Details", icon: "info", category: "inventory", source: "Inventory MCP" };
    return { name: "Inventory", icon: "inventory_2", category: "inventory", source: "Inventory MCP" };
  }

  // Fallback: clean up the name
  const cleaned = raw
    .replace(/^(work_orders|inventory)___/, "")
    .replace(/__.*$/, "")        // strip trailing path params like __work_order_id__get
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase()); // title-case
  return { name: cleaned || raw, icon: "build", category: "other", source: "Toolbox" };
}

function categoryColor(category: string): string {
  switch (category) {
    case "skill":
      return "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300";
    case "knowledge":
      return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300";
    case "work-orders":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300";
    case "inventory":
      return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300";
    case "discovery":
      return "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300";
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
  }
}

function statusMeta(status: ActivityEvent["status"]): {
  icon: string;
  color: string;
  label: string;
} {
  switch (status) {
    case "pending":
      return { icon: "hourglass_empty", color: "text-yellow-500", label: "Pending" };
    case "running":
      return { icon: "sync", color: "text-blue-500 animate-spin", label: "Running" };
    case "complete":
      return { icon: "check_circle", color: "text-green-500", label: "Done" };
    case "error":
      return { icon: "error", color: "text-red-500", label: "Error" };
  }
}

/** Parse args JSON and return meaningful key-value entries */
function parseArgs(raw: string | undefined, toolName: string): Array<[string, string]> | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;

    const lower = toolName.toLowerCase();

    // tool_search: just show the natural-language query
    if (lower === "tool_search") {
      const out: Array<[string, string]> = [];
      if (parsed.query) out.push(["query", String(parsed.query).slice(0, 120)]);
      return out.length > 0 ? out : null;
    }

    // call_tool fallback (gateway normally unwraps): show the wrapped target + args
    if (lower === "call_tool") {
      const out: Array<[string, string]> = [];
      if (parsed.name) out.push(["target", String(parsed.name)]);
      if (parsed.arguments && typeof parsed.arguments === "object") {
        for (const [k, v] of Object.entries(parsed.arguments)) {
          if (v === null || v === undefined) continue;
          const val = typeof v === "object" ? JSON.stringify(v) : String(v);
          out.push([k, val.length > 80 ? val.slice(0, 80) + "…" : val]);
        }
      }
      return out.length > 0 ? out : null;
    }

    // For knowledge base, the raw args may be huge — just show we queried it
    if (lower.includes("knowledge_base")) {
      const query = parsed.query || parsed.search || parsed.question;
      if (query) return [["query", String(query).slice(0, 80)]];
      return null;
    }

    const entries = Object.entries(parsed)
      .filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== "")
      .map(([k, v]) => {
        const val = typeof v === "object" ? JSON.stringify(v) : String(v);
        return [k, val.length > 80 ? val.slice(0, 80) + "…" : val] as [string, string];
      });
    return entries.length > 0 ? entries : null;
  } catch {
    return null;
  }
}

/** Create a short, readable version of the raw MCP tool name */
function shortenToolName(raw: string): string {
  // Strip MCP server prefix (e.g. "work_orders___" or "inventory___")
  const name = raw.replace(/^[a-z_]+___/, "");
  // FastAPI-style tools repeat the resource name: e.g.
  // "get_work_order_work_orders__work_order_id__get" — the second occurrence of
  // a word marks the start of the auto-generated route/method suffix, so truncate
  // before it to keep just "<verb>_<resource>".
  const parts = name.split("_").filter(Boolean);
  for (let i = 1; i < parts.length; i++) {
    for (let j = 0; j < i; j++) {
      if (parts[i] === parts[j]) {
        return parts.slice(0, i).join("_");
      }
    }
  }
  // Otherwise strip a trailing HTTP verb if present
  const verbMatch = name.match(/^(.*?)_(get|put|post|patch|delete)$/i);
  if (verbMatch && verbMatch[1]) return verbMatch[1];
  return name;
}

/** Try to extract context like WO ID from the detail field */
function extractDetailContext(activity: ActivityEvent): Array<[string, string]> | null {
  const detail = activity.detail ?? "";
  // First try structured format: "Calling tool (key=value)"
  const kvMatch = detail.match(/\((\w+)=([^)]+)\)/);
  if (kvMatch && kvMatch[1] && kvMatch[2]) return [[kvMatch[1], kvMatch[2]]];
  // Fallback: scan for known ID patterns
  const woMatch = detail.match(/WO-\d+/i);
  if (woMatch) return [["work_order", woMatch[0]]];
  const partMatch = detail.match(/FIB-\d+/i);
  if (partMatch) return [["part_id", partMatch[0]]];
  return null;
}

/** Extract skill name from args or detail field */
function getSkillName(activity: ActivityEvent): string | null {
  // Try args first
  if (activity.args) {
    try {
      const parsed = JSON.parse(activity.args);
      if (parsed.skill_name) return parsed.skill_name;
    } catch { /* ignore */ }
  }
  // Fallback: extract from detail string like "Loading skill: knowledge-retrieval"
  const match = (activity.detail ?? "").match(/Loading skill:\s*(.+)/i);
  return match?.[1]?.trim() ?? null;
}

export default function ActivitySidebar({ activities, isStreaming, onClear }: ActivitySidebarProps) {
  const completed = activities.filter((a) => a.status === "complete").length;
  const running = activities.filter((a) => a.status === "running").length;
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [width, setWidth] = useState(288); // 18rem = 288px default
  const isResizing = useRef(false);

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizing.current = true;
    const startX = e.clientX;
    const startWidth = width;

    const onMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      // Dragging left increases width (sidebar is on the right)
      const newWidth = Math.max(220, Math.min(600, startWidth + (startX - e.clientX)));
      setWidth(newWidth);
    };

    const onMouseUp = () => {
      isResizing.current = false;
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  }, [width]);

  return (
    <div
      className="relative flex flex-col border-l border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-900/80"
      style={{ width: `${width}px`, minWidth: "220px", maxWidth: "600px" }}
    >
      {/* Resize handle */}
      <div
        className="absolute left-0 top-0 bottom-0 z-20 w-1 cursor-col-resize hover:bg-blue-400/40 active:bg-blue-500/50"
        onMouseDown={startResize}
      />
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <span className="material-icons-outlined text-[18px] text-gray-500 dark:text-gray-400">
          timeline
        </span>
        <h2 className="text-sm font-semibold">Activity</h2>
        {isStreaming && (
          <span className="ml-auto inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
            <span className="material-icons-outlined animate-spin text-[14px]">sync</span>
            Working
          </span>
        )}
        {!isStreaming && activities.length > 0 && onClear && (
          <button
            type="button"
            onClick={onClear}
            className="ml-auto inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] text-gray-500 transition-colors hover:bg-gray-200 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
          >
            <span className="material-icons-outlined text-[14px]">delete_sweep</span>
            Clear
          </button>
        )}
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        {activities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <span className="material-icons-outlined text-[32px] text-gray-300 dark:text-gray-700">
              hub
            </span>
            <p className="mt-2 text-xs text-gray-400 dark:text-gray-600">
              Tool calls will appear here
            </p>
          </div>
        ) : (
          <div className="relative space-y-1">
            {/* Timeline line */}
            <div className="absolute left-[15px] top-2 bottom-2 w-px bg-gray-200 dark:bg-gray-700" />

            {(() => {
              // Build set of tool names that were actually invoked in this turn so
              // we can mark tool_search results that the model chose to use.
              const invokedToolNames = new Set(
                activities
                  .map((a) => a.tool)
                  .filter(
                    (t) =>
                      t &&
                      t !== "tool_search" &&
                      t !== "call_tool" &&
                      t !== "load_skill",
                  ),
              );
              return activities.map((activity) => {
              const tool = parseToolInfo(activity.tool);
              const status = statusMeta(activity.status);
              const isExpanded = expandedIds.has(activity.id);
              const isSkill = tool.category === "skill";
              const skillName = isSkill ? getSkillName(activity) : null;
              const argEntries = !isSkill ? parseArgs(activity.args, activity.tool) : null;

              return (
                <div key={activity.id} className="relative">
                  <button
                    type="button"
                    onClick={() => toggleExpand(activity.id)}
                    className={`relative flex w-full items-start gap-2.5 rounded-lg px-1.5 py-1.5 text-left transition-colors cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800/60 ${
                      isExpanded ? "bg-gray-100 dark:bg-gray-800/60" : ""
                    }`}
                  >
                    {/* Status dot */}
                    <div className="z-10 flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-white dark:bg-gray-900">
                      <span className={`material-icons-outlined text-[16px] ${status.color}`}>
                        {status.icon}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium ${categoryColor(tool.category)}`}>
                          <span className="material-icons-outlined text-[13px]">{tool.icon}</span>
                          {tool.name}
                        </span>
                        {activity.tool === "tool_search" && activity.results && activity.results.length > 0 && (() => {
                          const usedCount = activity.results.filter((r) => invokedToolNames.has(r.name)).length;
                          return (
                            <span
                              className="inline-flex items-center gap-0.5 rounded bg-indigo-50 px-1 py-0.5 text-[10px] font-medium text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300"
                              title={`${usedCount} of ${activity.results.length} returned tools were used`}
                            >
                              {usedCount > 0 ? `${usedCount} selected` : `${activity.results.length} found`}
                            </span>
                          );
                        })()}
                        <span className="material-icons-outlined ml-auto text-[14px] text-gray-400 dark:text-gray-600">
                          {isExpanded ? "expand_less" : "expand_more"}
                        </span>
                      </div>
                    </div>
                  </button>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div className="ml-[30px] mt-1 mb-2 rounded-lg border border-gray-200 bg-white px-3 py-2 dark:border-gray-700 dark:bg-gray-800">
                      {isSkill ? (
                        /* Skill call */
                        <div className="flex items-center gap-2 text-[11px]">
                          <span className="material-icons-outlined text-[14px] text-purple-500">auto_awesome</span>
                          <span className="font-medium text-gray-700 dark:text-gray-300">
                            {skillName || activity.detail || activity.tool}
                          </span>
                        </div>
                      ) : (() => {
                        const displayArgs = argEntries || extractDetailContext(activity);
                        return (
                        /* Tool call */
                        <div className="space-y-1.5">
                          {/* Source + short tool name */}
                          <div className="flex items-center gap-1.5">
                            <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-700 dark:text-gray-400">
                              <span className="material-icons-outlined text-[11px]">dns</span>
                              {tool.source}
                            </span>
                            <span className="font-mono text-[10px] text-gray-500 dark:text-gray-400">
                              {shortenToolName(activity.tool)}
                            </span>
                            <span className={`ml-auto shrink-0 text-[10px] ${
                              activity.status === "complete" ? "text-green-500" : "text-gray-400"
                            }`}>
                              {activity.status === "complete" ? "done" : activity.status}
                            </span>
                          </div>
                          {/* Args or extracted context */}
                          {displayArgs && (
                            <div className="space-y-0.5 border-t border-gray-100 pt-1.5 dark:border-gray-700">
                              {displayArgs.map(([key, val]) => (
                                <div key={key} className="flex items-baseline gap-1.5 text-[11px]">
                                  <span className="shrink-0 font-medium text-gray-500 dark:text-gray-400">{key}:</span>
                                  <span className="break-all text-gray-700 dark:text-gray-300">{val}</span>
                                </div>
                              ))}
                            </div>
                          )}
                          {/* tool_search results — only show ones the model actually used */}
                          {activity.tool === "tool_search" && activity.results && activity.results.length > 0 && (() => {
                            const usedResults = activity.results.filter((r) => invokedToolNames.has(r.name));
                            const totalCount = activity.results.length;
                            return (
                              <div className="space-y-1 border-t border-gray-100 pt-1.5 dark:border-gray-700">
                                <div className="text-[10px] font-medium uppercase tracking-wide text-gray-400 dark:text-gray-500">
                                  {usedResults.length > 0
                                    ? `Selected (${usedResults.length} of ${totalCount})`
                                    : `Returned ${totalCount}, none used yet`}
                                </div>
                                <div className="space-y-1">
                                  {usedResults.map((r) => (
                                    <div
                                      key={r.name}
                                      className="rounded border border-green-200 bg-green-50 px-2 py-1 dark:border-green-700/50 dark:bg-green-900/20"
                                    >
                                      <div className="flex items-baseline gap-1.5">
                                        <span className="material-icons-outlined text-[11px] text-green-600 dark:text-green-400">
                                          check_circle
                                        </span>
                                        <span className="font-mono text-[10px] font-semibold break-all text-gray-800 dark:text-gray-100">
                                          {shortenToolName(r.name)}
                                        </span>
                                      </div>
                                      {r.description && (
                                        <div className="mt-0.5 pl-[18px] text-[10px] leading-snug text-gray-500 dark:text-gray-400">
                                          {r.description}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                        );
                      })()}
                    </div>
                  )}
                </div>
              );
            });
            })()}
          </div>
        )}
      </div>

      {/* Footer stats */}
      <div className="border-t border-gray-200 px-4 py-2 dark:border-gray-800">
        <div className="flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <span className="material-icons-outlined text-[13px]">check_circle</span>
            {completed}
          </span>
          <span className="flex items-center gap-1">
            <span className="material-icons-outlined text-[13px]">sync</span>
            {running}
          </span>
          <span className="flex items-center gap-1">
            <span className="material-icons-outlined text-[13px]">tag</span>
            {activities.length}
          </span>
        </div>
      </div>
    </div>
  );
}
