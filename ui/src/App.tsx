import { useState } from "react";
import { useChat } from "./hooks/useChat";
import { useTheme } from "./hooks/useTheme";
import ChatPanel from "./components/ChatPanel";
import ActivitySidebar from "./components/ActivitySidebar";

export default function App() {
  const { messages, activities, isStreaming, send, resetChat, clearActivities } = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { theme, toggle: toggleTheme } = useTheme();

  return (
    <div className="flex h-screen flex-col bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-950">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Fibey Field Ops</h1>
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900 dark:text-blue-300">
            Foundry Toolbox Demo
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            <span className="material-icons-outlined text-[18px]">
              {theme === "dark" ? "light_mode" : "dark_mode"}
            </span>
          </button>
          <button
            onClick={resetChat}
            className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
          >
            <span className="material-icons-outlined text-[18px]">add_comment</span>
            New Chat
          </button>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
          >
            <span className="material-icons-outlined text-[18px]">
              {sidebarOpen ? "visibility_off" : "visibility"}
            </span>
            {sidebarOpen ? "Hide" : "Show"} Activity
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex min-h-0 flex-1">
        <ChatPanel
          messages={messages}
          isStreaming={isStreaming}
          onSend={send}
        />
        {sidebarOpen && (
          <ActivitySidebar
            activities={activities}
            isStreaming={isStreaming}
            onClear={clearActivities}
          />
        )}
      </div>
    </div>
  );
}
