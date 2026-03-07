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
- **DB**: PostgreSQL + SQLAlchemy 2.0 async + Alembic
- **AI**: Pydantic AI agents (vendor-agnostic, model via `PYDANTIC_AI_MODEL` env var)
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

- RAG/pgvector deferred — game rules are short enough to pass as full context to LLM
- Tutorials are pre-authored JSON (no LLM call needed), stored in DB
- Chat uses SSE streaming via `sse-starlette`
- Conversation history managed server-side (not sent from client)
- Vision uses Pydantic AI VisionAgent with multimodal model support
- Voice uses Web Speech API (STT) with cloud TTS fallback

## Demo Games

Catan, Ticket to Ride, Wingspan — each has tutorial JSON, setup checklist, and quick reference data.
