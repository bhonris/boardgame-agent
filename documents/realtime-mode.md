# Realtime Mode

## Feature Specification

Realtime mode is a seamless, immersive experience that mimics having a real game master sitting at the table. The user sees a live camera feed of the board, voice is always active (continuous listening after toggle), and AI responses are automatically spoken aloud. No tabs, no typing — just natural conversation while looking at the game.

## Scope

### In Scope
- New "Realtime" tab in GameView alongside existing tabs
- Live camera feed always visible as the main view
- Continuous voice recognition (auto-restarts after each utterance, no push-to-talk)
- Auto TTS — AI responses are spoken automatically without user action
- Floating chat transcript overlay on top of camera feed
- Periodic camera snapshots sent to vision API for context-aware responses
- "Snap & Ask" — user can say something while looking at the board, and the AI sees what they see
- Toggle to activate/deactivate realtime session
- Visual indicators for listening state, AI thinking, and speaking state

### Out of Scope
- Multi-user / multi-device sync
- Video streaming to backend (snapshots only)
- Custom wake words
- Background noise filtering (rely on browser Speech API)
- Saving/replaying realtime sessions

## User Stories

- As a player learning a new game, I want to point my phone at the board and ask questions naturally so I don't have to type or switch tabs
- As a player mid-game, I want the AI to see my board state when I ask "what should I do next?" so it gives contextual advice
- As a group of players, I want hands-free voice interaction so nobody has to stop playing to use the app

## Acceptance Criteria

1. Realtime tab appears in GameView navigation
2. Entering Realtime tab requests camera permission and starts live feed
3. A prominent toggle button activates/deactivates the realtime session
4. When active: voice recognition is continuous (restarts automatically after each final result)
5. When active: user speech is transcribed, sent to chat API with a camera snapshot attached for context
6. When active: AI response is automatically spoken via TTS (cloud first, browser fallback)
7. When active: visual indicators show current state (listening / processing / speaking)
8. Chat transcript floats over the camera feed, auto-scrolls, semi-transparent background
9. User can deactivate to pause — camera stays on but voice stops
10. Leaving the Realtime tab stops camera and voice
11. All interactions are saved to the same chat session for continuity

## Architecture & Technical Design

### Frontend Components

```
GameView
  └── RealtimeMode (new)
        ├── Live camera feed (<video> element, always visible)
        ├── RealtimeControls (activate/deactivate toggle, state indicators)
        ├── RealtimeTranscript (floating overlay of conversation)
        └── Uses continuous SpeechRecognition + auto TTS
```

**RealtimeMode component:**
- Manages camera stream lifecycle (start on mount, stop on unmount)
- Manages continuous SpeechRecognition loop
- On final speech result: captures camera frame → sends message + image to backend
- On AI response complete: auto-plays TTS, then resumes listening
- State machine: `idle` → `listening` → `processing` → `speaking` → `listening` (loop)

### Backend Changes

**New endpoint: `POST /api/games/{game_id}/chat/realtime`**
- Accepts multipart form: `message` (text), `image` (file, optional), `session_id` (optional)
- Combines vision context + chat in a single call
- Returns SSE stream (same format as existing chat)
- System prompt enhanced for realtime context: "You are sitting at the table with the player. They are showing you the board. Keep responses concise and conversational — they will be spoken aloud."

**AI Service addition:**
- `get_realtime_agent()` — new agent with realtime-specific system prompt
- Shorter, more conversational responses optimized for TTS
- Accepts optional image context inline

### State Flow

```
[Idle] --toggle on--> [Listening] --speech detected--> [Processing]
  ^                                                        |
  |                   [Speaking] <--response ready----------
  |                      |
  +---toggle off---------+--utterance done--> [Listening]
```

## API Contract

### POST /api/games/{game_id}/chat/realtime

**Request:** multipart/form-data
- `message`: string (required) — transcribed speech
- `image`: file (optional) — JPEG camera snapshot
- `session_id`: string (optional) — existing session ID

**Response:** SSE stream
- `event: chunk` → `{"text": "..."}`
- `event: done` → `{"session_id": "...", "citations": []}`
- `event: error` → `{"error": "..."}`

## Database Changes

None — reuses existing ChatSession and ChatMessage tables. The session mode can be set to a new `realtime` value.

**Migration:** Add `realtime` to ChatMode enum.

## UI/UX Considerations

- Camera feed fills the content area (16:9 or full-width)
- Transcript overlay: bottom portion of screen, semi-transparent dark background, white text
- Max 5-6 recent messages visible in overlay (older messages scroll off)
- State indicator: colored dot/ring around activate button
  - Gray: inactive
  - Green pulsing: listening
  - Yellow: processing
  - Blue pulsing: speaking
- Activate button is large and centered below camera feed
- Mobile-first: works well in portrait with phone pointed at board

## Security Considerations

- Camera/microphone permissions handled via browser APIs (user must grant)
- Image snapshots are sent as JPEG, same validation as existing vision endpoint
- No persistent image storage — images processed and discarded
- Rate limiting on realtime endpoint to prevent abuse

## Performance Considerations

- Camera snapshots captured at reduced resolution (640x480) to minimize upload size
- JPEG quality 0.6 for snapshots (good enough for board game recognition)
- Debounce: don't send image if last snapshot was < 2 seconds ago
- TTS audio pre-fetched while streaming text to reduce latency
- SpeechRecognition restart has minimal gap between utterances

## Edge Cases & Error Handling

- Camera permission denied → show message, allow text-only realtime mode
- Speech recognition not supported → show message, fall back to regular chat
- TTS fails → continue without audio, show text response
- Network error during streaming → show error in transcript, resume listening
- User speaks while AI is speaking → stop TTS, process new input
- Very long AI response → cap TTS at reasonable length, show full text in transcript
- Browser tab hidden → pause recognition (resume on focus)

## Testing Strategy

- Unit tests for RealtimeMode component (mock camera, speech, fetch)
- Unit tests for realtime API endpoint
- Integration test: message + image → SSE response
- Test state machine transitions (idle → listening → processing → speaking → listening)
- Test cleanup on unmount (camera stopped, recognition stopped)

## Dependencies

- No new packages needed
- Uses existing: Web Speech API, MediaDevices API, SSE streaming, OpenAI TTS

## Migration & Rollback Plan

- Backend: Add `realtime` to ChatMode enum (additive, no breaking change)
- Frontend: New component + new tab (no changes to existing components)
- Rollback: Remove tab entry, endpoint is unused

## Open Questions

- None currently

## Todo List

- [x] Create feature specification
- [x] Backend: Add `realtime` to ChatMode enum
- [x] Backend: Create `get_realtime_agent()` in ai_service.py
- [x] Backend: Create `POST /api/games/{game_id}/chat/realtime` endpoint
- [x] Backend: Update SessionService to accept mode parameter
- [x] Frontend: Add `realtime` tab to GameView
- [x] Frontend: Update gameStore with realtime tab type
- [x] Frontend: Create RealtimeMode component
- [x] Frontend: Add `streamChatRealtime()` to API client
- [x] Tests: Backend endpoint tests (5 tests)
- [x] Tests: Frontend component tests (12 tests + 2 store tests)
- [x] Update CLAUDE.md files
