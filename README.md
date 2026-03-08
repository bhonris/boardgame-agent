# AI Board Game Teacher

An AI-powered board game teaching assistant that helps players learn games like Catan, Ticket to Ride, and Wingspan through interactive tutorials, chat, and board state analysis.

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js 20+](https://nodejs.org/)
- [pnpm](https://pnpm.io/installation)
- [PostgreSQL](https://www.postgresql.org/download/)
- An API key for your chosen LLM provider (OpenAI or Anthropic)

## Project Structure

```
packages/
  api/          # Python FastAPI backend
  web/          # React + TypeScript + Vite frontend
documents/      # Feature specs
```

## Getting Started

### 1. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE boardgame;
```

### 2. Backend Setup

```bash
cd packages/api

# Install dependencies
uv sync

# Copy the example env file and fill in your values
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/boardgame
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/boardgame
PYDANTIC_AI_MODEL=openai:gpt-4o
VISION_MODEL=openai:gpt-4o
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
CORS_ORIGINS=["http://localhost:5173"]
```

You only need the API key for the provider you're using. The model is vendor-agnostic via [Pydantic AI](https://ai.pydantic.dev/) — set `PYDANTIC_AI_MODEL` to any supported model string (e.g., `anthropic:claude-sonnet-4-20250514`).

Run database migrations:

```bash
.venv/Scripts/python.exe -m alembic upgrade head    # Windows
# .venv/bin/python -m alembic upgrade head           # macOS/Linux
```

Start the API server:

```bash
.venv/Scripts/python.exe -m uvicorn main:app --reload    # Windows
# .venv/bin/python -m uvicorn main:app --reload           # macOS/Linux
```

The API will be available at `http://localhost:8000`.

### 3. Frontend Setup

```bash
cd packages/web

# Install dependencies
pnpm install

# Start the dev server
pnpm dev
```

The app will be available at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend at `localhost:8000`.

## Running Tests

### Backend

```bash
cd packages/api
.venv/Scripts/python.exe -m pytest tests/ -v    # Windows
# .venv/bin/python -m pytest tests/ -v           # macOS/Linux
```

### Frontend

```bash
cd packages/web
pnpm test              # single run
pnpm test:watch        # watch mode
pnpm test:coverage     # with coverage report
```

## Tech Stack

### Backend
- **FastAPI** with async SQLAlchemy 2.0 and PostgreSQL
- **Pydantic AI** for vendor-agnostic LLM integration
- **Alembic** for database migrations
- **SSE** (Server-Sent Events) for streaming chat responses

### Frontend
- **React 19** with TypeScript
- **Vite** for dev server and builds
- **Tailwind CSS v4** for styling
- **Zustand** for state management
- **React Query** for server state
- **Web Speech API** for voice input
