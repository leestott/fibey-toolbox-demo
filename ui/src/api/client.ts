export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ToolSearchResult {
  name: string;
  description: string;
}

export interface ActivityEvent {
  id: string;
  tool: string;
  call_id?: string;
  status: "pending" | "running" | "complete" | "error";
  detail: string;
  timestamp: number;
  args?: string;
  result?: string;
  results?: ToolSearchResult[];
}

export interface StreamCallbacks {
  onDelta: (content: string) => void;
  onActivity: (event: Omit<ActivityEvent, "id" | "timestamp">) => void;
  onError: (message: string) => void;
  onDone: () => void;
}

export async function sendMessage(
  message: string,
  sessionId: string,
  callbacks: StreamCallbacks
): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    callbacks.onError(`Request failed: ${response.status}`);
    callbacks.onDone();
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError("No response body");
    callbacks.onDone();
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const raw = line.slice(6);

        if (currentEvent === "done" || raw === "[DONE]") {
          callbacks.onDone();
          return;
        }

        try {
          const data = JSON.parse(raw) as Record<string, unknown>;
          switch (currentEvent) {
            case "delta":
              callbacks.onDelta((data["content"] as string) ?? "");
              break;
            case "activity":
              callbacks.onActivity({
                tool: (data["tool"] as string) ?? "",
                call_id: data["call_id"] as string | undefined,
                status: (data["status"] ?? "running") as ActivityEvent["status"],
                detail: (data["detail"] as string) ?? "",
                args: data["args"] as string | undefined,
                result: data["result"] as string | undefined,
                results: Array.isArray(data["results"])
                  ? (data["results"] as ToolSearchResult[])
                  : undefined,
              });
              break;
            case "error":
              callbacks.onError((data["message"] as string) ?? "Unknown error");
              break;
          }
        } catch {
          // Skip malformed JSON
        }

        currentEvent = "";
      }
    }
  }

  callbacks.onDone();
}

export async function resetSession(sessionId: string): Promise<void> {
  await fetch("/api/sessions/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
}
