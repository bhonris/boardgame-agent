# Web Package (packages/web)

React + TypeScript frontend for the AI Board Game Teacher.

## Quick Reference

- **Dev server**: `pnpm dev` (runs on http://localhost:5173, proxies `/api` and `/images` to localhost:8000)
- **Build**: `pnpm build`
- **Tests**: `pnpm test` (single run) | `pnpm test:watch` (watch mode) | `pnpm test:coverage`
- **Lint**: `pnpm lint`
- **Install deps**: `pnpm install`

## Project Layout

```
src/
  main.tsx               # App entry point, renders <App />
  App.tsx                # Root component — QueryClientProvider, routes between GameSelection and GameView
  index.css              # Global styles (Tailwind CSS v4)
  test-setup.ts          # Vitest setup (jsdom environment)
  api/
    client.ts            # API client functions (fetchGames, streamChat, analyzeImage, textToSpeech)
  components/
    GameSelection.tsx    # Game picker grid
    GameView.tsx         # Main game view with tabbed interface
    TutorialEngine.tsx   # Step-by-step tutorial player
    ChatInterface.tsx    # Streaming chat with SSE
    QuickReference.tsx   # Reference cards display
    CameraCapture.tsx    # Camera/image upload for vision analysis
    VoiceInterface.tsx   # Voice input (Web Speech API) and TTS playback
    SetupChecklist.tsx   # Game setup verification
    __tests__/           # Component tests
  stores/
    gameStore.ts         # Zustand store (selectedGame, session, messages, tutorial step, active tab)
    __tests__/           # Store tests
  hooks/                 # Custom React hooks
  types/
    game.ts              # TypeScript types (Game, TutorialData, ChatMessage, etc.)
    speech.d.ts          # Web Speech API type declarations
  assets/                # Static assets
vite.config.ts           # Vite config with React plugin, Tailwind, proxy, and Vitest settings
```

## Key Conventions

- **State management**: Zustand for client state (game selection, chat messages, UI state)
- **Server state**: React Query (`@tanstack/react-query`) with 5-minute stale time
- **API calls**: All go through `src/api/client.ts`, using `/api` prefix (proxied to backend)
- **Chat streaming**: Uses SSE — `streamChat()` returns an async generator yielding `{ event, data }` objects
- **Styling**: Tailwind CSS v4 (utility classes, no component library)
- **Testing**: Vitest + React Testing Library + jsdom
- **No routing library for pages**: App uses Zustand `selectedGame` state to switch between GameSelection and GameView (react-router-dom is installed but not actively used for page routing)

## Component Architecture

```
App
├── GameSelection          # When no game selected
└── GameView               # When a game is selected
    ├── TutorialEngine     # Tab: tutorial
    ├── ChatInterface      # Tab: chat
    ├── CameraCapture      # Tab: camera
    ├── QuickReference     # Tab: reference
    ├── SetupChecklist     # Setup verification
    └── VoiceInterface     # Voice input overlay
```

## API Client Functions

| Function | Method | Endpoint |
|---|---|---|
| `fetchGames()` | GET | `/api/games` |
| `fetchGame(id)` | GET | `/api/games/{id}` |
| `fetchTutorial(id)` | GET | `/api/games/{id}/tutorial` |
| `fetchReference(id)` | GET | `/api/games/{id}/reference` |
| `streamChat(id, msg, sessionId?)` | POST | `/api/games/{id}/chat` |
| `analyzeImage(id, file, mode, sessionId?)` | POST | `/api/games/{id}/vision` |
| `textToSpeech(text, voice?)` | POST | `/api/tts` |
