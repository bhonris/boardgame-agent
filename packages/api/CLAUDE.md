# API Package (packages/api)

Python FastAPI backend for the AI Board Game Teacher.

## Quick Reference

- **Run server**: `.venv/Scripts/python.exe -m uvicorn main:app --reload` (Windows)
- **Run tests**: `.venv/Scripts/python.exe -m pytest tests/ -v`
- **Run migrations**: `.venv/Scripts/python.exe -m alembic upgrade head`
- **Create migration**: `.venv/Scripts/python.exe -m alembic revision --autogenerate -m "description"`
- **Seed data**: `.venv/Scripts/python.exe seed_data.py`
- **Install deps**: `/c/Python314/python.exe -m uv add <package> --directory .`

## Project Layout

```
main.py                  # FastAPI app entry point, mounts routers and static files
app/
  config.py              # Settings via pydantic-settings, reads from .env
  database.py            # Async SQLAlchemy engine and session factory (SQLite + aiosqlite)
  models/
    base.py              # All ORM models (Game, GameRulebook, RulebookChunk,
                         #   TutorialScript, QuickReference, ChatSession, ChatMessage)
  schemas/
    game.py              # Pydantic request/response schemas
  routers/
    games.py             # GET /api/games, /api/games/{id}, /{id}/tutorial, /{id}/reference
    chat.py              # POST /api/games/{id}/chat — SSE streaming chat
    vision.py            # POST /api/games/{id}/vision — image analysis (identify, read_card, verify_setup)
    tts.py               # POST /api/tts — text-to-speech via OpenAI
  services/
    ai_service.py        # Pydantic AI agents (teacher_agent, vision_agent)
    session_service.py   # Chat session and message persistence
    rulebook_ingestion.py # PDF rulebook processing
    embedding_service.py # Embedding generation (unused — RAG deferred)
    rag_service.py       # RAG retrieval (unused — RAG deferred)
alembic/
  env.py                 # Alembic config (strips +aiosqlite for sync driver)
  versions/              # Migration files
data/
  images/                # Static game images served at /images
  tutorials/             # Pre-authored tutorial JSON files (one per game)
tests/
  conftest.py            # Test fixtures (async SQLite in-memory DB, FastAPI test client)
  test_database.py       # DB query + service tests (33 tests)
  test_schemas.py        # Schema validation tests
  test_ingestion.py      # Rulebook ingestion tests
  test_config.py         # Config tests
```

## Key Conventions

- **Async everywhere**: All DB operations use async SQLAlchemy with `aiosqlite`
- **Portable types**: Models use `JSON` (not JSONB), `String(36)` PKs (not UUID), `native_enum=False`
- **ChatMessage PK**: Auto-incrementing integer for reliable ordering
- **Dependency injection**: Database sessions via `Depends(get_db)`
- **Model prefix**: All API routes start with `/api/`
- **Vendor-agnostic AI**: Model is configured via `PYDANTIC_AI_MODEL` env var, not hardcoded
- **Chat streaming**: Uses SSE via `sse-starlette`, events are `chunk`, `error`, `done`
- **Conversation history**: Managed server-side in `chat_sessions` / `chat_messages` tables
- **Static files**: Game images served from `data/images/` mounted at `/images`

## Environment Variables

See `.env.example` for all available variables. Key ones:

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLite async connection string (default: `sqlite+aiosqlite:///./boardgame.db`) |
| `PYDANTIC_AI_MODEL` | LLM model identifier (default: `openai:gpt-5-nano`) |
| `VISION_MODEL` | Model for image analysis (default: `openai:gpt-5-nano`) |
| `OPENAI_API_KEY` | Required for OpenAI models and TTS |
| `CORS_ORIGINS` | JSON array of allowed origins |

## Database Models

- **Game** — board game metadata (id is a string slug like `catan`)
- **GameRulebook** — processed rulebook text with status tracking
- **RulebookChunk** — chunked rulebook text (for future RAG)
- **TutorialScript** — pre-authored JSON tutorial steps (JSON `steps` column)
- **QuickReference** — reference cards (turn_order, icons, scoring, setup)
- **ChatSession** — tracks a conversation with mode (qa, tutorial, dispute)
- **ChatMessage** — individual messages with auto-increment PK, role, content, and model tracking
