import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "../api/client";

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

/** A parsed <details> block */
interface DetailsBlock {
  summary: string;
  content: string;
}

/** Segment: either plain markdown or a details block */
type Segment =
  | { type: "markdown"; content: string }
  | { type: "details"; summary: string; content: string };

/**
 * Split markdown into segments of plain text and <details> blocks,
 * so each part can be rendered through ReactMarkdown independently.
 */
function splitDetailsBlocks(md: string): Segment[] {
  const segments: Segment[] = [];
  const pattern = /<details>\s*\n?\s*<summary>(.*?)<\/summary>\s*\n?([\s\S]*?)<\/details>/gi;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(md)) !== null) {
    // Text before this <details>
    if (match.index > lastIndex) {
      const before = md.slice(lastIndex, match.index).trim();
      if (before) segments.push({ type: "markdown", content: before });
    }
    segments.push({
      type: "details",
      summary: (match[1] ?? "").trim(),
      content: (match[2] ?? "").trim(),
    });
    lastIndex = match.index + match[0].length;
  }

  // Remaining text after last <details>
  if (lastIndex < md.length) {
    const remaining = md.slice(lastIndex).trim();
    if (remaining) segments.push({ type: "markdown", content: remaining });
  }

  // If no details blocks found, return the whole thing as markdown
  if (segments.length === 0) {
    segments.push({ type: "markdown", content: md });
  }

  return segments;
}

/** Collapsible details component */
function CollapsibleDetails({ summary, content }: DetailsBlock) {
  const [open, setOpen] = useState(false);

  return (
    <div className={`details-block ${open ? "is-open" : ""}`}>
      <button
        className="details-summary"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <span className="material-icons-outlined details-chevron">
          expand_more
        </span>
        {summary}
      </button>
      {open && (
        <div className="details-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}

/**
 * Splits markdown content into main body and a list of source names.
 * Handles multiple formats:
 *   1. --- separator + Sources heading + 📄 bullet list
 *   2. Inline 📄 Sources: comma-separated
 *   3. **Sources** / ## Sources heading + bullet list (markdown format)
 */
function extractSources(content: string): {
  body: string;
  sources: string[];
} {
  // Format 1: --- separator + Sources heading + 📄 bullet list
  const structuredPattern =
    /\n---\n\s*\*{0,2}Sources?\*{0,2}\s*\n((?:\s*[-*]\s*📄?\s*.+\n?)+)$/i;
  const structuredMatch = content.match(structuredPattern);
  if (structuredMatch) {
    const body = content.slice(0, structuredMatch.index ?? 0).trimEnd();
    const sources = (structuredMatch[1] ?? "")
      .split("\n")
      .map((line) => line.replace(/^\s*[-*]\s*📄?\s*/, "").trim())
      .filter(Boolean);
    return { body, sources };
  }

  // Format 3: **Sources** or ## Sources heading followed by bullet list at end
  const headingPattern =
    /\n+(?:\*{1,2}Sources?\*{1,2}|#{1,3}\s+Sources?)\s*\n((?:\s*[-*]\s*.+\n?)+)$/i;
  const headingMatch = content.match(headingPattern);
  if (headingMatch) {
    const body = content.slice(0, headingMatch.index ?? 0).trimEnd();
    const sources = (headingMatch[1] ?? "")
      .split("\n")
      .map((line) => line.replace(/^\s*[-*]\s*📄?\s*/, "").trim())
      .filter(Boolean);
    return { body, sources };
  }

  // Format 2: inline 📄 Sources: comma-separated
  const inlinePattern = /\n?📄\s*\*{0,2}Sources?\*{0,2}:\s*(.+)$/i;
  const inlineMatch = content.match(inlinePattern);
  if (inlineMatch) {
    const names = (inlineMatch[1] ?? "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    return { body: content.slice(0, inlineMatch.index ?? 0).trimEnd(), sources: names };
  }

  return { body: content, sources: [] };
}

/**
 * During streaming, strip any incomplete <details> block at the end
 * so it doesn't flash as raw markup before being reformatted.
 */
function stripIncompleteDetails(md: string): string {
  // Count open vs close tags
  const opens = (md.match(/<details>/gi) || []).length;
  const closes = (md.match(/<\/details>/gi) || []).length;
  if (opens <= closes) return md;
  // There's an unclosed <details> — remove everything from the last unclosed one
  const lastOpen = md.lastIndexOf("<details>");
  if (lastOpen === -1) return md;
  return md.slice(0, lastOpen).trimEnd();
}

export default function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const { body, sources } = isUser
    ? { body: message.content, sources: [] }
    : extractSources(message.content);

  // During streaming, hide incomplete <details> blocks to prevent flicker
  const cleanBody = isStreaming ? stripIncompleteDetails(body) : body;
  const segments = isUser ? [] : splitDetailsBlocks(cleanBody);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} gap-3`}>
      {/* Avatar */}
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 shadow-sm">
          <span className="material-icons-outlined text-[18px] text-white">cable</span>
        </div>
      )}

      <div
        className={`rounded-2xl px-5 py-3 ${
          isUser
            ? "max-w-[75%] bg-blue-600 text-white"
            : "max-w-[85%] bg-gray-50 text-gray-900 ring-1 ring-gray-200 dark:bg-gray-800/80 dark:text-gray-100 dark:ring-gray-700"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        ) : (
          <>
            <div className="markdown-body">
              {segments.map((seg, i) =>
                seg.type === "markdown" ? (
                  <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
                    {seg.content}
                  </ReactMarkdown>
                ) : (
                  <CollapsibleDetails
                    key={i}
                    summary={seg.summary}
                    content={seg.content}
                  />
                )
              )}
            </div>

            {sources.length > 0 && (
              <div className="sources-section">
                <div className="sources-label">Sources</div>
                <ul className="sources-list">
                  {sources.map((src, i) => (
                    <li key={i}>
                      <span className="source-pill">
                        <span className="material-icons-outlined source-icon">description</span>
                        {src}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>

      {/* Spacer for user messages (keeps alignment) */}
      {isUser && <div className="w-8 shrink-0" />}
    </div>
  );
}
