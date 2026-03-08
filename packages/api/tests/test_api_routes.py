"""Tests for API route handlers — verifies endpoints return correct responses."""
import io
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import (
    ChatMode,
    ChatSession,
    Game,
    GameRulebook,
    QuickReference,
    ReferenceType,
    RulebookStatus,
    TutorialScript,
)


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, app_client: AsyncClient):
        response = await app_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestListGames:
    @pytest.mark.asyncio
    async def test_list_games_empty(self, app_client: AsyncClient):
        response = await app_client.get("/api/games")
        assert response.status_code == 200
        assert response.json() == {"games": []}

    @pytest.mark.asyncio
    async def test_list_games_returns_active_only(
        self, app_client: AsyncClient, db: AsyncSession, sample_games
    ):
        response = await app_client.get("/api/games")
        assert response.status_code == 200
        data = response.json()
        titles = [g["title"] for g in data["games"]]
        assert "Catan" in titles
        assert "Wingspan" in titles
        assert "Inactive Game" not in titles

    @pytest.mark.asyncio
    async def test_list_games_response_shape(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        response = await app_client.get("/api/games")
        game = response.json()["games"][0]
        assert "id" in game
        assert "title" in game
        assert "min_players" in game
        assert "max_players" in game


class TestGetGame:
    @pytest.mark.asyncio
    async def test_get_game_by_id(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        response = await app_client.get("/api/games/catan")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "catan"
        assert data["title"] == "Catan"

    @pytest.mark.asyncio
    async def test_get_game_not_found(self, app_client: AsyncClient):
        response = await app_client.get("/api/games/nonexistent")
        assert response.status_code == 404


class TestGetTutorial:
    @pytest.mark.asyncio
    async def test_get_tutorial(
        self, app_client: AsyncClient, db: AsyncSession, sample_tutorial
    ):
        response = await app_client.get("/api/games/catan/tutorial")
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "catan"
        assert data["total_steps"] == 2
        assert len(data["steps"]) == 2

    @pytest.mark.asyncio
    async def test_tutorial_not_found(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        response = await app_client.get("/api/games/catan/tutorial")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_tutorial_step_fields(
        self, app_client: AsyncClient, db: AsyncSession, sample_tutorial
    ):
        response = await app_client.get("/api/games/catan/tutorial")
        step = response.json()["steps"][0]
        assert "id" in step
        assert "phase" in step
        assert "title" in step
        assert "content" in step
        assert "estimated_seconds" in step


class TestGetReference:
    @pytest.mark.asyncio
    async def test_get_references(
        self, app_client: AsyncClient, db: AsyncSession, sample_references
    ):
        response = await app_client.get("/api/games/catan/reference")
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "catan"
        assert len(data["references"]) == 2

    @pytest.mark.asyncio
    async def test_references_ordered(
        self, app_client: AsyncClient, db: AsyncSession, sample_references
    ):
        response = await app_client.get("/api/games/catan/reference")
        refs = response.json()["references"]
        assert refs[0]["display_order"] < refs[1]["display_order"]

    @pytest.mark.asyncio
    async def test_references_not_found(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        response = await app_client.get("/api/games/catan/reference")
        assert response.status_code == 404


class TestChatValidation:
    @pytest.mark.asyncio
    async def test_chat_missing_message(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        response = await app_client.post(
            "/api/games/catan/chat",
            json={},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_game_not_found(self, app_client: AsyncClient):
        response = await app_client.post(
            "/api/games/nonexistent/chat",
            json={"message": "hello"},
        )
        assert response.status_code == 404


class TestAgentLazyInit:
    """Regression: agents must not be created at import time (crashes when no API key)."""

    @pytest.mark.asyncio
    async def test_import_ai_service_without_api_key(self, monkeypatch):
        """Importing ai_service should not create Agent objects eagerly."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        # Clear cached agents so they'd be recreated
        from app.services import ai_service

        ai_service.get_teacher_agent.cache_clear()
        ai_service.get_vision_agent.cache_clear()

        # Re-importing should not raise — agents are lazy
        import importlib
        importlib.reload(ai_service)
        # Module loaded without error — no Agent created at import time

    @pytest.mark.asyncio
    async def test_agent_uses_output_type_not_result_type(self):
        """Regression: pydantic-ai v1.x renamed result_type to output_type."""
        import os
        os.environ.setdefault("OPENAI_API_KEY", "test-key")
        from app.services.ai_service import get_teacher_agent, get_vision_agent

        get_teacher_agent.cache_clear()
        get_vision_agent.cache_clear()

        # These should not raise "Unknown keyword arguments: result_type"
        teacher = get_teacher_agent()
        vision = get_vision_agent()
        assert teacher is not None
        assert vision is not None


class TestTTSValidation:
    @pytest.mark.asyncio
    async def test_tts_no_api_key(self, app_client: AsyncClient, monkeypatch):
        monkeypatch.setattr("app.routers.tts.settings", type("S", (), {"openai_api_key": ""})())
        response = await app_client.post("/api/tts", json={"text": "hello"})
        assert response.status_code == 503


def _make_mock_realtime_agent(response_text: str = "Hello from realtime!"):
    """Create a mock realtime agent that streams the given response text."""
    mock_agent = MagicMock()
    mock_result = MagicMock()

    async def mock_stream_text(delta=True):
        for word in response_text.split():
            yield word + " "

    mock_result.stream_text = mock_stream_text

    @asynccontextmanager
    async def mock_run_stream(*args, **kwargs):
        yield mock_result

    mock_agent.run_stream = mock_run_stream
    return mock_agent


class TestChatRealtime:
    @pytest.mark.asyncio
    async def test_chat_realtime_text_only(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Send text message without image, verify SSE response with chunk and done events."""
        mock_agent = _make_mock_realtime_agent("This is a test response")
        with patch("app.routers.chat.get_realtime_agent", return_value=mock_agent):
            response = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "How do I play?"},
            )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Parse SSE events from response body
        body = response.text
        events = _parse_sse_events(body)

        chunk_events = [e for e in events if e["event"] == "chunk"]
        done_events = [e for e in events if e["event"] == "done"]

        assert len(chunk_events) >= 1
        # Each chunk should have text data
        for chunk in chunk_events:
            data = json.loads(chunk["data"])
            assert "text" in data

        assert len(done_events) == 1
        done_data = json.loads(done_events[0]["data"])
        assert "session_id" in done_data
        assert "citations" in done_data

    @pytest.mark.asyncio
    async def test_chat_realtime_with_image(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Send text message with a JPEG image, verify SSE response."""
        mock_agent = _make_mock_realtime_agent("I can see the board")
        # Create a minimal JPEG-like binary payload
        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100

        with patch("app.routers.chat.get_realtime_agent", return_value=mock_agent):
            response = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "What do you see?"},
                files={"image": ("board.jpg", io.BytesIO(fake_jpeg), "image/jpeg")},
            )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        events = _parse_sse_events(response.text)
        chunk_events = [e for e in events if e["event"] == "chunk"]
        done_events = [e for e in events if e["event"] == "done"]

        assert len(chunk_events) >= 1
        assert len(done_events) == 1

    @pytest.mark.asyncio
    async def test_chat_realtime_game_not_found(self, app_client: AsyncClient):
        """Request with nonexistent game_id returns 404."""
        response = await app_client.post(
            "/api/games/nonexistent/chat/realtime",
            data={"message": "hello"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_realtime_creates_session(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Verify a new session with realtime mode is created when none exists."""
        mock_agent = _make_mock_realtime_agent("Welcome!")
        with patch("app.routers.chat.get_realtime_agent", return_value=mock_agent):
            response = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Hi there"},
            )
        assert response.status_code == 200

        events = _parse_sse_events(response.text)
        done_events = [e for e in events if e["event"] == "done"]
        assert len(done_events) == 1
        session_id = json.loads(done_events[0]["data"])["session_id"]

        # Verify session exists in DB with realtime mode
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        assert session is not None
        assert session.mode == ChatMode.realtime
        assert session.game_id == "catan"

    @pytest.mark.asyncio
    async def test_chat_realtime_reuses_session(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Verify existing session is reused when session_id is provided."""
        mock_agent = _make_mock_realtime_agent("First reply")

        # First request — creates a session
        with patch("app.routers.chat.get_realtime_agent", return_value=mock_agent):
            response1 = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "First message"},
            )
        events1 = _parse_sse_events(response1.text)
        session_id = json.loads(
            [e for e in events1 if e["event"] == "done"][0]["data"]
        )["session_id"]

        # Second request — reuse the same session
        mock_agent2 = _make_mock_realtime_agent("Second reply")
        with patch("app.routers.chat.get_realtime_agent", return_value=mock_agent2):
            response2 = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Second message", "session_id": session_id},
            )
        events2 = _parse_sse_events(response2.text)
        session_id_2 = json.loads(
            [e for e in events2 if e["event"] == "done"][0]["data"]
        )["session_id"]

        assert session_id == session_id_2

        # Verify session message count increased (2 user + 2 assistant = 4)
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one()
        assert session.message_count == 4


def _parse_sse_events(body: str) -> list[dict]:
    """Parse SSE text into a list of {event, data} dicts."""
    events = []
    current_event = None
    current_data = None
    for line in body.splitlines():
        if line.startswith("event:"):
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            current_data = line[len("data:"):].strip()
        elif line == "" and current_event is not None:
            events.append({"event": current_event, "data": current_data})
            current_event = None
            current_data = None
    # Handle final event without trailing blank line
    if current_event is not None and current_data is not None:
        events.append({"event": current_event, "data": current_data})
    return events


class TestChatRealtimeImageFormat:
    """Regression: image must be passed as BinaryContent, not raw dicts."""

    @pytest.mark.asyncio
    async def test_chat_realtime_image_uses_binary_content(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Verify the agent receives a list with BinaryContent when image is provided."""
        from pydantic_ai.messages import BinaryContent

        captured_prompt = None
        mock_agent = MagicMock()
        mock_result = MagicMock()

        async def mock_stream_text(delta=True):
            yield "OK "

        mock_result.stream_text = mock_stream_text

        @asynccontextmanager
        async def mock_run_stream(prompt, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            yield mock_result

        mock_agent.run_stream = mock_run_stream

        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100

        with patch("app.routers.chat.get_realtime_agent", return_value=mock_agent):
            response = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "What is this?"},
                files={"image": ("board.jpg", io.BytesIO(fake_jpeg), "image/jpeg")},
            )
        assert response.status_code == 200

        # Prompt must be a list: [str, BinaryContent], NOT raw dicts
        assert isinstance(captured_prompt, list), "Prompt should be a list when image is provided"
        assert len(captured_prompt) == 2
        assert isinstance(captured_prompt[0], str)
        assert isinstance(captured_prompt[1], BinaryContent)
        assert captured_prompt[1].media_type == "image/jpeg"

    @pytest.mark.asyncio
    async def test_chat_realtime_text_only_passes_string_prompt(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Verify the agent receives a plain string prompt when no image is provided."""
        captured_prompt = None
        mock_agent = MagicMock()
        mock_result = MagicMock()

        async def mock_stream_text(delta=True):
            yield "OK "

        mock_result.stream_text = mock_stream_text

        @asynccontextmanager
        async def mock_run_stream(prompt, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            yield mock_result

        mock_agent.run_stream = mock_run_stream

        with patch("app.routers.chat.get_realtime_agent", return_value=mock_agent):
            response = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "How do I play?"},
            )
        assert response.status_code == 200
        assert isinstance(captured_prompt, str), "Prompt should be a plain string when no image"


class TestVisionImageFormat:
    """Regression: vision endpoint must pass BinaryContent, not raw dicts."""

    @pytest.mark.asyncio
    async def test_vision_image_uses_binary_content(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Verify the vision agent receives BinaryContent, not OpenAI-style dicts."""
        from pydantic_ai.messages import BinaryContent

        captured_prompt = None
        mock_agent = MagicMock()
        mock_run_result = MagicMock()
        mock_run_result.data = "It's a game piece."

        async def mock_run(prompt, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return mock_run_result

        mock_agent.run = AsyncMock(side_effect=mock_run)

        fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100

        with patch("app.routers.vision.get_vision_agent", return_value=mock_agent):
            response = await app_client.post(
                "/api/games/catan/vision",
                data={"mode": "identify"},
                files={"image": ("board.jpg", io.BytesIO(fake_jpeg), "image/jpeg")},
            )
        assert response.status_code == 200

        # Prompt must be a list: [str, BinaryContent]
        assert isinstance(captured_prompt, list)
        assert len(captured_prompt) == 2
        assert isinstance(captured_prompt[0], str)
        assert isinstance(captured_prompt[1], BinaryContent)
        assert captured_prompt[1].media_type == "image/jpeg"
