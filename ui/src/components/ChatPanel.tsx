import { useEffect, useRef } from "react";
import type { ChatMessage } from "../api/client";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import PromptSuggestions from "./PromptSuggestions";

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (text: string) => void;
}

export default function ChatPanel({ messages, isStreaming, onSend }: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-1 flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 bg-white dark:bg-gray-950">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-gray-400 dark:text-gray-600">
                Fibey Agent
              </h2>
              <p className="mt-2 text-sm text-gray-400 dark:text-gray-600">
                Ask me anything — I'll use the Foundry Toolbox to help.
              </p>
            </div>
            <div className="mt-8 w-full max-w-2xl">
              <PromptSuggestions onSelect={onSend} />
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {messages
              .filter((msg) => msg.role === "user" || msg.content)
              .map((msg) => (
              <MessageBubble key={msg.id} message={msg} isStreaming={isStreaming && msg === messages[messages.length - 1]} />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-500" />
                Agent working…
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={isStreaming} />
    </div>
  );
}
