# AI Board Game Teacher

## Feature Specification

Board game cafes stock hundreds of games but have limited staff who can teach them all. Customers stick to familiar games instead of exploring the full library because learning complex games from a rulebook is painful. We're building an AI-powered, vendor-agnostic teaching assistant that helps customers learn any board game through guided tutorials, conversational Q&A, camera-based component identification, and voice interaction. For the PoC, the primary target is a laptop with webcam; the system is designed to also work on cafe-owned tablets for future deployment.

## Scope

### In Scope (Proof of Concept)
- Responsive web app (PWA) — **laptop with webcam as primary PoC target**, tablet-ready for future deployment
- AI-guided step-by-step tutorials for 3-5 demo games
- Free-form Q&A powered by RAG over digitized rulebooks
- Camera-based features via laptop webcam: component identification, card reading, setup verification
- Voice interaction: push-to-talk voice input (STT) and spoken responses (TTS) for hands-free use
- Quick reference cards (turn order, icon glossary, scoring)
- Interactive setup checklists
- Streaming chat responses for natural conversation feel

### Out of Scope
- Multi-tenant SaaS / admin dashboard
- Subscription billing
- Customer phone support (QR code flow)
- Game recommendation engine
- POS/booking system integration
- Offline mode
- Multiplayer device sync

## User Stories

- **As a customer**, I want to pick a game off the shelf and have an AI walk me through setup and rules step-by-step, so I don't need to wait for staff or read a 20-page rulebook.
- **As a customer**, I want to ask "Can I do X?" during gameplay and get an accurate, cited answer immediately, so the game doesn't stall while we argue about rules.
- **As a customer**, I want to point the tablet camera at a game piece and have the AI tell me what it is and how it works, so I can understand unfamiliar components.
- **As a customer**, I want a persistent quick-reference card showing turn order, icons, and scoring, so I don't have to re-ask the same questions.
- **As a customer**, I want to ask questions by voice while my hands are busy holding cards or moving pieces, so I don't have to stop playing to type.
- **As a cafe owner**, I want customers to explore more of my game library without consuming staff time, so I can serve more tables and increase customer satisfaction.

## Acceptance Criteria

- [ ] User can select a game from a list and start a guided tutorial
- [ ] Tutorial walks through setup, theme/goal, components, turn structure, core actions, and a first-round walkthrough in progressive steps
- [ ] User can ask free-form questions at any point and receive accurate answers grounded in rulebook content
- [ ] AI responses cite rulebook sections/page numbers when applicable
- [ ] Camera capture works via laptop webcam (and tablet camera) — user can photograph a component and get identification + explanation
- [ ] Quick reference cards display correctly for each supported game
- [ ] Setup checklist is interactive (checkable items)
- [ ] Chat responses stream in real-time (not delayed until complete)
- [ ] User can ask questions by voice (push-to-talk) and hear AI responses spoken aloud
- [ ] Voice transcript is displayed as text so all players can follow along
- [ ] UI is responsive — works on laptop browsers and tablet screens, with 48px minimum tap targets
- [ ] All features work for at least 3 demo games (e.g., Catan, Ticket to Ride, Wingspan)

## Architecture & Technical Design

### System Overview

```
[Cafe Tablet (PWA)]
        |  (HTTPS)
        v
[API Server - FastAPI/Python]
    |           |           |
    v           v           v
[PostgreSQL]  [pgvector]  [Pydantic AI → Any LLM]
(game data,   (rulebook   (Claude, GPT, Gemini,
 sessions)    embeddings)  etc. — vendor agnostic)
```

### Frontend — React + TypeScript + Vite (PWA)

- **Framework**: React 19 + TypeScript, built with Vite, pnpm
- **Styling**: Tailwind CSS with touch-optimized components
- **State**: Zustand for client state, React Query for server state
- **PWA**: Service worker for fast loading, installable on tablets

Key features/pages:
| Feature | Component | Description |
|---------|-----------|-------------|
| Game Selection | `GameSelection.tsx` | Grid of available games with cover art, player count, complexity, play time |
| Tutorial Engine | `TutorialEngine.tsx` | Progressive step-by-step teaching UI with progress indicator |
| Chat / Q&A | `ChatInterface.tsx` | Conversational UI with streaming responses, available anytime |
| Camera | `CameraCapture.tsx` | Device camera for component ID, card reading, setup verification |
| Voice | `VoiceInterface.tsx` | Push-to-talk voice input, spoken AI responses, visual transcript |
| Quick Reference | `QuickReference.tsx` | Persistent tab with turn order, icon glossary, scoring |

### Backend — Python (FastAPI + Pydantic AI)

- **Runtime**: Python 3.12+
- **Framework**: FastAPI
- **LLM Orchestration**: Pydantic AI (vendor-agnostic — swap models via env var)
- **Database**: PostgreSQL + pgvector extension
- **ORM**: SQLAlchemy 2.0 + Alembic for migrations
- **Package manager**: uv
- **Streaming**: Server-Sent Events (SSE) via FastAPI `StreamingResponse`

Key endpoints:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/games` | GET | List available games |
| `/api/games/:id` | GET | Game details + metadata |
| `/api/games/:id/tutorial` | GET | Tutorial steps for a game |
| `/api/games/:id/reference` | GET | Quick reference data |
| `/api/games/:id/chat` | POST | Q&A conversation (streaming SSE) |
| `/api/games/:id/vision` | POST | Camera image analysis |
| `/api/tts` | POST | Cloud text-to-speech (optional, for higher-quality voice output) |

### AI Layer — Pydantic AI (Vendor Agnostic)

All LLM interactions go through **Pydantic AI**, making the system model-agnostic. Swap from Claude to GPT-4o, Gemini, or any supported model by changing one environment variable (`PYDANTIC_AI_MODEL`).

**1. AI Service (`ai_service.py`)** — Pydantic AI agents with typed inputs/outputs:
- `TeacherAgent` — main agent with "board game teacher" system prompt, game-specific context via dependencies, RAG tool for rulebook retrieval. Returns structured `TeachingResponse` with text + citations.
- `VisionAgent` — handles image analysis for component ID, card reading, setup verification. Accepts image input via multimodal model support.
- Agents use `agent.run_stream()` for real-time streaming to the frontend.
- Testing uses Pydantic AI's `TestModel` / `FunctionModel` — deterministic tests without API calls.

**2. RAG Service (`rag_service.py`)**
- Embeds user queries via a configurable embedding provider (default: OpenAI text-embedding-3-small, swappable via config — Pydantic AI handles LLM agents, but embeddings use a separate thin abstraction layer)
- Performs vector similarity search against pgvector (per-game namespace)
- Assembles relevant rulebook chunks as context
- Exposed as a Pydantic AI **tool** that agents call for retrieval

**3. Rulebook Ingestion Service (`rulebook_ingestion.py`)**
- Processes uploaded rulebook PDFs
- Pipeline: PDF → text extraction (PyMuPDF) → section detection → semantic chunking (~500 tokens) → embedding → pgvector storage

**AI Teaching Methodology:**
The tutorial follows how experienced human teachers explain games:
1. **Theme & Goal** (30s) — What's the game about? How do you win?
2. **Components Overview** — What's on the table, what each piece type does
3. **Turn Structure** — What happens on your turn, in order
4. **Core Actions** — The 2-3 most important things you can do
5. **First Round Walkthrough** — Play through Round 1 together
6. **Advanced Rules** — Introduced just-in-time as they become relevant

Key principle: **teach the minimum needed to start playing, then introduce rules as they become relevant.**

**Vision Features** (via VisionAgent — works with any multimodal model):
- "What is this piece?" — Point camera at a component, AI identifies and explains it
- "Read this card" — Capture a card with small text, AI reads and explains effects
- "Is our setup correct?" — Capture board state, AI verifies against correct setup

## API Contract

### GET /api/games
```json
// Response 200
{
  "games": [
    {
      "id": "catan",
      "title": "Catan",
      "coverImageUrl": "/images/catan.jpg",
      "minPlayers": 3,
      "maxPlayers": 4,
      "complexityWeight": 2.3,
      "playTimeMinutes": 90,
      "description": "Trade, build, and settle the island of Catan."
    }
  ]
}
```

### GET /api/games/:id/tutorial
```json
// Response 200
{
  "gameId": "catan",
  "steps": [
    {
      "id": 1,
      "phase": "theme_and_goal",
      "title": "What is Catan?",
      "content": "You're settlers on the island of Catan...",
      "imageUrl": "/images/catan/overview.jpg",
      "estimatedSeconds": 30
    }
  ],
  "totalSteps": 12,
  "estimatedMinutes": 15
}
```

### POST /api/games/:id/chat
```json
// Request
{
  "sessionId": "uuid",
  "message": "Can I trade with the bank?"
}
// Note: conversation history is managed server-side per session, not sent from client

// Response: SSE stream
// event: chunk
// data: {"text": "Yes! You can trade with the bank at a 4:1 ratio..."}
// event: done
// data: {"citations": [{"page": 8, "section": "Trading"}]}
```

### POST /api/games/:id/vision
```json
// Request (multipart/form-data)
{
  "image": <file>,
  "mode": "identify" | "read_card" | "verify_setup",
  "sessionId": "uuid"
}

// Response 200
{
  "analysis": "This is a Settlement piece (orange). Settlements are placed at intersections...",
  "confidence": "high",
  "relatedRules": ["Settlements cost 1 brick, 1 lumber, 1 wool, 1 grain..."]
}
```

## Database Changes

### Schema (SQLAlchemy 2.0 + pgvector)

```
Game
  id (text, PK), title, bgg_id, publisher, year,
  min_players, max_players, complexity_weight, play_time_minutes,
  description, cover_image_url, is_active, created_at

GameRulebook
  id (uuid, PK), game_id (FK), version, source_pdf_url,
  processed_text, section_structure (jsonb), status (enum: processing/ready/error),
  created_at

RulebookChunk
  id (uuid, PK), rulebook_id (FK), game_id (FK), section_name,
  chunk_text, chunk_index, embedding (vector(1536)), token_count, created_at

TutorialScript
  id (uuid, PK), game_id (FK), version, steps (jsonb),
  estimated_duration_minutes, is_curated (boolean), created_at

QuickReference
  id (uuid, PK), game_id (FK), type (enum: turn_order/icons/scoring/setup),
  content (jsonb), display_order, created_at

ChatSession
  id (uuid, PK), game_id (FK), device_id, mode (enum: tutorial/qa/dispute),
  started_at, ended_at, message_count, rating (int, nullable)

ChatMessage
  id (uuid, PK), session_id (FK), role (enum: user/assistant),
  content (text), rag_chunks_used (jsonb), model_used, token_count, created_at
```

Greenfield project. Initial schema creation via Alembic migrations.

## UI/UX Considerations

- **Responsive layout**: Laptop-first for PoC (mouse + keyboard), with touch-friendly sizing (48px tap targets) for future tablet deployment
- **Readable UI**: High contrast, readable fonts (16px minimum body text) — works in dim cafe lighting
- **Desktop + tablet**: Layout works well at both laptop (1280px+) and tablet (1024px landscape) widths
- **Tutorial progress**: Clear step indicator (e.g., "Step 3 of 12") with back/forward navigation
- **Chat always accessible**: Floating "Ask a Question" button available on every screen
- **Camera UX**: Large capture button, preview before sending, clear loading state while AI processes
- **Loading states**: Skeleton screens for initial load, streaming text for AI responses
- **Error states**: Friendly messages ("I'm not sure about that rule — you may want to check page 8 of the rulebook")

## Security Considerations

- No user authentication for table-side usage (tablet/laptop is the trust boundary)
- CORS configured to allow only the frontend origin (Vite dev server in dev, production domain in prod)
- API rate limiting to prevent abuse (per device ID / IP)
- Image uploads validated (file type, max size 10MB) and not stored long-term
- Conversation history managed server-side (not sent from client — prevents tampering and reduces payload size)
- No PII collected from customers
- Rulebook content never exposed raw — only AI-synthesized answers with citations
- API keys (Anthropic, OpenAI, etc.) stored in environment variables via pydantic-settings, never client-side

## Performance Considerations

- **Streaming responses**: SSE ensures users see text appearing immediately, not waiting 5-10s for complete response
- **Pre-cached tutorials**: Tutorial steps are pre-authored JSON, loaded instantly (no LLM call needed)
- **Vector search latency**: pgvector with HNSW index, target < 100ms for similarity search
- **Image processing**: Camera images resized client-side before upload to reduce transfer time
- **PWA caching**: Game catalog, tutorial scripts, and reference cards cached in service worker for instant loading

## Edge Cases & Error Handling

- **AI gives wrong rule**: Responses include citations; add a "Flag this answer" button for feedback
- **Game not in system**: Show friendly "This game isn't available yet" with option to request it
- **Camera fails**: Graceful fallback to text-based Q&A ("Describe the piece you're looking at")
- **Network loss**: Cached tutorial steps and reference cards remain available; chat shows "Reconnecting..." state
- **Ambiguous rules**: AI should acknowledge ambiguity ("The rulebook isn't clear on this. The most common interpretation is...")
- **Multiple editions**: Rulebook version tracked per game; AI should note if there are known edition differences

## Testing Strategy

### Unit Tests (pytest + vitest)
- RAG pipeline: chunking logic, embedding mock, context assembly, relevance ranking
- Pydantic AI agents: using `TestModel`/`FunctionModel` for deterministic tests without API calls
- Tutorial step engine: step progression, state management (frontend vitest)
- API route handlers: request validation, response formatting (httpx test client)
- Voice hooks: STT/TTS hook behavior (frontend vitest)

### Integration Tests
- Full chat flow: question → RAG retrieval → agent → streamed SSE response
- Rulebook ingestion: PDF → chunks → embeddings → stored in pgvector
- Vision flow: image upload → VisionAgent → structured response
- Session management: conversation history persisted and retrieved correctly
- Model swapping: verify agents work with at least 2 model configurations

### E2E Tests
- Load demo game → start tutorial → navigate all steps → ask a question → receive accurate answer
- Camera capture → component identification → correct explanation

### Manual Verification
- Test with 3-5 real games, cross-check AI answers against actual rulebooks
- Test on laptop with webcam (primary PoC target) — verify camera, voice, and full user flow
- Future: test on tablet hardware in cafe-like conditions (dim lighting, shared use)

**Target: 95%+ test coverage**

## Dependencies

### Frontend (npm/pnpm)
- react, react-dom, vite, tailwindcss, zustand, @tanstack/react-query, vite-plugin-pwa, typescript, vitest

### Backend (Python/uv)
- pydantic-ai (vendor-agnostic LLM orchestration)
- fastapi, uvicorn (web framework + ASGI server)
- sqlalchemy[asyncio], alembic (ORM + migrations)
- pgvector (PostgreSQL vector extension for SQLAlchemy)
- pymupdf (PDF text extraction)
- pydantic-settings (configuration)
- pytest, pytest-asyncio, httpx (testing)

### External Services
- **LLM provider** — Configured via `PYDANTIC_AI_MODEL` env var. Default: Claude (Anthropic). Swap to OpenAI, Google, Groq, etc. without code changes.
- **Embedding provider** — Configurable. Default: OpenAI text-embedding-3-small.
- **PostgreSQL** — with pgvector extension enabled

### Infrastructure (PoC)
- Local PostgreSQL or a managed instance (Supabase, Neon, Railway)
- Hosting: Vercel (frontend) + Railway/Render/Fly.io (backend) — or all local for demo

## Future Work (Post-PoC)

- **Proactive camera-based error detection**: AI continuously monitors the camera and intervenes when it detects illegal moves or mistakes. Deferred due to high complexity:
  - Requires a per-game rules engine to track game state across turns (essentially building a game engine for each supported game)
  - Continuous vision API calls cost ~$4-11/hour per table (unsustainable at scale)
  - Reliable object detection under variable lighting, camera angles, and hand occlusion is error-prone with high false-positive risk
  - Latency of 2-5 seconds per vision call means the player has likely moved on before feedback arrives
  - **PoC alternative**: The on-demand "Is our setup correct?" and "What is this piece?" features cover the most valuable use cases without these problems
  - **Revisit when**: Vision model costs drop significantly, or a lightweight local model can handle frame analysis without API calls
- **Game recommendation engine**: "We have 4 players and 90 minutes — what should we play?"
- **Multi-device sync**: All phones/tablets at the table see the same tutorial progress
- **Offline mode**: Full functionality without internet using local models
- **Publisher API integrations**: Official content from game publishers
- **Multi-tenant SaaS**: Admin dashboard, subscription billing, analytics for multiple cafes

## Migration & Rollback Plan

N/A for proof of concept — greenfield project with no production data. For future production deployment, Alembic migrations will handle schema changes.

## Open Questions

- [ ] **Rulebook licensing**: Is using digitized rulebooks for private RAG legally defensible as fair use? Should we pursue publisher partnerships from the start?
- [ ] **Which demo games?** Proposed: Catan, Ticket to Ride, Wingspan, Azul, Codenames — confirm with target cafe
- [ ] **Embedding model**: OpenAI text-embedding-3-small vs. an open-source alternative (reduces vendor dependency)?
- [ ] **Tablet hardware**: Specific tablet model recommendation for cafes? (iPad 10th gen vs. Samsung Galaxy Tab A9+)
- [ ] **Camera quality**: Are cafe lighting conditions sufficient for reliable component identification via tablet camera?

## Todo List

### Phase 1: Foundation & Infrastructure
- [ ] Create project scaffolding (packages/web with Vite+React+pnpm, packages/api with FastAPI+uv)
- [ ] Set up PostgreSQL with pgvector, define SQLAlchemy models, run initial Alembic migration
- [ ] Configure FastAPI with CORS (for cross-origin requests from Vite dev server)
- [ ] Build rulebook ingestion pipeline (PDF → PyMuPDF extraction → chunking → embeddings → pgvector)
- [ ] Implement RAG service (query embedding → vector search → context assembly)
- [ ] Implement AI service with Pydantic AI agents (TeacherAgent, VisionAgent) with configurable model
- [ ] Build thin embedding abstraction layer (default: OpenAI, swappable via config)
- [ ] Write unit tests for Phase 1 (RAG pipeline, ingestion, AI agents using TestModel)

### Phase 2: Core Teaching Experience
- [ ] Create tutorial scripts for 3-5 demo games (JSON format)
- [ ] Build Game Selection screen
- [ ] Build Tutorial Engine UI (step-by-step progressive teaching)
- [ ] Build Chat Interface UI (streaming Q&A via SSE)
- [ ] Build Quick Reference component
- [ ] Build Setup Checklist component
- [ ] Implement server-side session/conversation history management
- [ ] Write unit + integration tests for Phase 2 (tutorial engine, chat flow, API routes)

### Phase 3: Camera & Vision
- [ ] Build Camera Capture UI (component ID, card reading, setup verification)
- [ ] Integrate VisionAgent with multimodal model support (vendor-agnostic via Pydantic AI)
- [ ] Write tests for vision flow (image upload → VisionAgent → response)

### Phase 4: Voice Interaction
- [ ] Build Voice Interface (push-to-talk mic button, waveform indicator, transcript)
- [ ] Implement speech-to-text hook (Web Speech API, Whisper API fallback)
- [ ] Implement text-to-speech hook (Web Speech API + optional cloud TTS)
- [ ] Add cloud TTS endpoint on backend (if using higher-quality voice)
- [ ] Integrate voice into tutorial mode (read steps aloud) and Q&A mode
- [ ] Write tests for voice features (STT/TTS hooks, voice endpoint)

### Phase 5: Polish & Validation
- [ ] Write E2E tests (complete user journey across all modes)
- [ ] Manual testing with real games on laptop with webcam
- [ ] Cross-check AI answers against actual rulebooks for all demo games
- [ ] Test model swapping — verify the app works with at least 2 different LLM providers
- [ ] Performance optimization (streaming latency, image resize, PWA caching)
