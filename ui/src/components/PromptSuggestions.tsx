interface Suggestion {
  prompt: string;
  tags: { label: string; color: "red" | "green" | "yellow" }[];
}

const suggestions: Suggestion[] = [
  {
    prompt: "Pull up work order WO-003 and tell me what parts are needed.",
    tags: [
      { label: "work-order-preparation", color: "red" },
      { label: "Work Orders API", color: "green" },
      { label: "Inventory MCP", color: "yellow" },
    ],
  },
  {
    prompt: "Do we have OTDR test equipment in stock? What models are available?",
    tags: [
      { label: "inventory-lookup", color: "red" },
      { label: "Inventory MCP", color: "green" },
    ],
  },
  {
    prompt: "What are the proper procedures for fusion splicing single-mode fiber?",
    tags: [
      { label: "knowledge-retrieval", color: "red" },
      { label: "FoundryIQ", color: "green" },
    ],
  },
  {
    prompt:
      "Check the parts list for WO-005 and tell me if we have everything in stock.",
    tags: [
      { label: "work-order-preparation", color: "red" },
      { label: "Work Orders API", color: "green" },
      { label: "Inventory MCP", color: "yellow" },
    ],
  },
  {
    prompt:
      "What safety protocols should a technician review before performing aerial cable installation?",
    tags: [
      { label: "knowledge-retrieval", color: "red" },
      { label: "FoundryIQ", color: "green" },
    ],
  },
  {
    prompt:
      "Give me a full field briefing for WO-007 — parts availability, relevant procedures, and safety guidelines.",
    tags: [
      { label: "field-briefing", color: "red" },
      { label: "Work Orders API", color: "green" },
      { label: "Inventory MCP", color: "yellow" },
      { label: "FoundryIQ", color: "yellow" },
    ],
  },
];

const tagColors = {
  red: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
  green: "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300",
  yellow:
    "bg-yellow-50 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300",
};

interface PromptSuggestionsProps {
  onSelect: (prompt: string) => void;
}

export default function PromptSuggestions({ onSelect }: PromptSuggestionsProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {suggestions.map((s, i) => (
        <button
          key={i}
          onClick={() => onSelect(s.prompt)}
          className="group rounded-xl border border-gray-200 bg-white p-4 text-left transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-900"
        >
          <p className="text-sm text-gray-800 group-hover:text-gray-950 dark:text-gray-200 dark:group-hover:text-white">
            {s.prompt}
          </p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {s.tags.map((tag, j) => (
              <span
                key={j}
                className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${tagColors[tag.color]}`}
              >
                {tag.label}
              </span>
            ))}
          </div>
        </button>
      ))}
    </div>
  );
}
