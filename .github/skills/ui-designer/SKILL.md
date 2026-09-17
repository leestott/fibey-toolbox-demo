---
name: "UI Designer"
description: "React + TypeScript + Tailwind CSS chat interface specialist for this project's streaming chat UI"
tags: ['react', 'typescript', 'tailwind', 'ui', 'chat']
---

# UI Designer Skill

You are a specialist in building the chat interface for this project. Follow these patterns:

## Tech Stack
- React 18+ with functional components and hooks
- TypeScript (strict mode)
- Tailwind CSS v4 for styling (utility-first, no separate CSS files per component)
- Vite for dev server and bundling

## Component Patterns

### Chat Components
- `ChatPanel` — main container with message list, auto-scrolls to latest message
- `MessageBubble` — renders user (right-aligned, blue) and assistant (left-aligned, gray) messages
- `ChatInput` — input bar with send button, disabled while streaming
- `ActivitySidebar` — collapsible panel showing real-time tool invocations

### Message Rendering
- Use `react-markdown` with `remark-gfm` for assistant messages
- Support code blocks with syntax highlighting
- Handle streaming: messages append content as chunks arrive

### Streaming UX
- The frontend calls `POST /api/chat` and reads newline-delimited JSON events
- Parse event types: `message` (text chunks), `activity` (tool events), `citation` (sources)
- Show a typing indicator while streaming
- Activity events appear in the sidebar in real-time with status badges (pending → running → complete)

## File Organization
```
ui/src/
├── api/client.ts        # Streaming fetch client
├── components/          # React components
├── hooks/useChat.ts     # Chat state management
├── App.tsx              # Root layout
├── main.tsx             # Entry point
└── index.css            # Tailwind imports
```

## Styling Guidelines
- Use Tailwind utility classes exclusively
- Dark mode support via `dark:` variants
- Responsive: sidebar collapses on mobile
- Use `bg-white dark:bg-gray-900` base palette
- Smooth transitions for sidebar toggle and message appearance
