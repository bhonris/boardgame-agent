# AI Board Game Teacher

## Project Structure

```
packages/
  api/          # Python FastAPI backend
  web/          # React + TypeScript + Vite frontend
documents/      # Feature specs
```

## Backend (packages/api)

- **Runtime**: Python 3.12, FastAPI, managed with uv
- **DB**: SQLite (aiosqlite) + SQLAlchemy 2.0 async + Alembic
- **AI**: Pydantic AI agents (model via `PYDANTIC_AI_MODEL` env var, default: `openai:gpt-5-nano`)
- **Venv**: `.venv/` in packages/api, activate with `.venv/Scripts/python.exe` on Windows
- **Run tests**: `cd packages/api && .venv/Scripts/python.exe -m pytest tests/ -v`
- **Run server**: `cd packages/api && .venv/Scripts/python.exe -m uvicorn main:app --reload`
- **Key files**: `main.py` (app entry), `app/config.py` (settings), `app/models/base.py` (ORM models)

## Frontend (packages/web)

- **Stack**: React 19, TypeScript, Vite, Tailwind CSS v4, Zustand, React Query
- **Package manager**: pnpm
- **Run tests**: `cd packages/web && pnpm test`
- **Run dev**: `cd packages/web && pnpm dev` (proxies /api to localhost:8000)
- **Build**: `cd packages/web && pnpm build`

## Key Architecture Decisions

- SQLite for local dev (no external DB needed); models use portable types (JSON, String PKs, no PG-specific types)
- RAG deferred — game rules are short enough to pass as full context to LLM
- Tutorials are pre-authored JSON (no LLM call needed), stored in DB
- Chat uses SSE streaming via `sse-starlette`
- Conversation history managed server-side (not sent from client)
- Vision uses Pydantic AI VisionAgent with multimodal model support
- Voice uses Web Speech API (STT) with cloud TTS fallback
- Realtime mode: seamless camera + continuous voice + auto-TTS for hands-free game mastering

## Realtime Mode

- **Endpoint**: `POST /api/games/{game_id}/chat/realtime` (multipart: message, optional image, optional session_id)
- **Agent**: `get_realtime_agent()` in ai_service.py — short, conversational responses optimized for TTS
- **Frontend**: `RealtimeMode` component — live camera feed, continuous SpeechRecognition, auto-TTS
- **State machine**: idle → listening → processing → speaking → listening (loop)
- **Session mode**: `ChatMode.realtime` in DB

## Demo Games

Catan, Ticket to Ride, Wingspan, Splendor — each has tutorial JSON, setup checklist, and quick reference data.
