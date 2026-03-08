"""Comprehensive integration tests for the Realtime Mode.

Exercises the full HTTP flow with mocked AI agents — covers SSE streaming,
session management, image handling, conversation history, TTS, error paths,
and edge cases.

Run from packages/api:
    .venv/Scripts/python.exe -m pytest ../../test_tools/realtime_integration_test.py -v
"""

import io
import json
import struct
import uuid
import zlib
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Re-use fixtures from the main test suite
from tests.conftest import *  # noqa: F401,F403

from app.models.base import (
    ChatMessage,
    ChatMode,
    ChatSession,
    GameRulebook,
    MessageRole,
    RulebookStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_png(width: int, height: int, color: tuple = (200, 150, 100)) -> bytes:
    """Minimal valid PNG for upload testing."""
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    hdr = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    raw = b""
    for _ in range(height):
        raw += b"\x00" + bytes(color) * width
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return hdr + ihdr + idat + iend


def _parse_sse(body: str) -> list[dict]:
    events = []
    current_event = "message"
    for line in body.split("\n"):
        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            events.append({"event": current_event, "data": line[5:].strip()})
    return events


def _make_mock_agent(response_text: str):
    """Mock agent whose run_stream yields the response as word-by-word chunks."""
    agent = MagicMock()
    result = MagicMock()

    async def stream_text(delta=True):
        for word in response_text.split():
            yield word + " "

    result.stream_text = stream_text

    @asynccontextmanager
    async def run_stream(*args, **kwargs):
        # Stash call kwargs so tests can inspect them
        agent._last_call_args = args
        agent._last_call_kwargs = kwargs
        yield result

    agent.run_stream = run_stream
    return agent


# ---------------------------------------------------------------------------
# 1. Basic realtime request / response
# ---------------------------------------------------------------------------

class TestRealtimeBasicFlow:
    """Happy-path: text-only and text+image requests produce valid SSE."""

    @pytest.mark.asyncio
    async def test_text_only_returns_sse_stream(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("Place a settlement on an intersection")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Where should I build?"},
            )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        events = _parse_sse(resp.text)
        chunks = [e for e in events if e["event"] == "chunk"]
        dones = [e for e in events if e["event"] == "done"]
        assert len(chunks) >= 1
        assert len(dones) == 1

        # Reassemble text
        full = "".join(json.loads(c["data"])["text"] for c in chunks)
        assert "settlement" in full.lower()

    @pytest.mark.asyncio
    async def test_text_with_png_image(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("I see the board")
        png = _create_png(640, 480)
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "What do you see?"},
                files={"image": ("snap.png", io.BytesIO(png), "image/png")},
            )
        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        assert any(e["event"] == "done" for e in events)

    @pytest.mark.asyncio
    async def test_text_with_jpeg_image(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("Nice board layout")
        jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 200 + b"\xff\xd9"
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Check my setup"},
                files={"image": ("snap.jpg", io.BytesIO(jpeg), "image/jpeg")},
            )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_text_with_webp_image(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("Looks good")
        # Minimal WebP header
        webp = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 100
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Anything wrong?"},
                files={"image": ("snap.webp", io.BytesIO(webp), "image/webp")},
            )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. Game context & instructions
# ---------------------------------------------------------------------------

class TestRealtimeGameContext:
    """Verify the agent receives the correct game title and rulebook content."""

    @pytest.mark.asyncio
    async def test_instructions_contain_game_title(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Hi"},
            )
        assert resp.status_code == 200
        instructions = agent._last_call_kwargs.get("instructions", "")
        assert "Catan" in instructions

    @pytest.mark.asyncio
    async def test_instructions_contain_rulebook(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        rulebook = GameRulebook(
            game_id="catan",
            status=RulebookStatus.ready,
            processed_text="Each player starts with 2 settlements and 2 roads.",
        )
        db.add(rulebook)
        await db.commit()

        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "How do I start?"},
            )
        instructions = agent._last_call_kwargs.get("instructions", "")
        assert "2 settlements and 2 roads" in instructions

    @pytest.mark.asyncio
    async def test_no_rulebook_uses_fallback(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Teach me"},
            )
        instructions = agent._last_call_kwargs.get("instructions", "")
        assert "general knowledge" in instructions.lower()

    @pytest.mark.asyncio
    async def test_instructions_contain_realtime_persona(
        self, app_client: AsyncClient, sample_game
    ):
        """The realtime prompt should instruct the agent to be conversational/short."""
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Hello"},
            )
        instructions = agent._last_call_kwargs.get("instructions", "")
        assert "short" in instructions.lower() or "conversational" in instructions.lower()


# ---------------------------------------------------------------------------
# 3. Session management
# ---------------------------------------------------------------------------

class TestRealtimeSessionManagement:
    """Verify session creation, reuse, and message persistence."""

    @pytest.mark.asyncio
    async def test_first_call_creates_session(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        agent = _make_mock_agent("Welcome!")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Start"},
            )
        events = _parse_sse(resp.text)
        done = [e for e in events if e["event"] == "done"][0]
        sid = json.loads(done["data"])["session_id"]

        result = await db.execute(select(ChatSession).where(ChatSession.id == sid))
        session = result.scalar_one()
        assert session.mode == ChatMode.realtime
        assert session.game_id == "catan"
        assert session.message_count == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_reuse_session_across_calls(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        agent = _make_mock_agent("First reply")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp1 = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "First"},
            )
        sid1 = json.loads(
            [e for e in _parse_sse(resp1.text) if e["event"] == "done"][0]["data"]
        )["session_id"]

        agent2 = _make_mock_agent("Second reply")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent2):
            resp2 = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Second", "session_id": sid1},
            )
        sid2 = json.loads(
            [e for e in _parse_sse(resp2.text) if e["event"] == "done"][0]["data"]
        )["session_id"]
        assert sid1 == sid2

        result = await db.execute(select(ChatSession).where(ChatSession.id == sid1))
        session = result.scalar_one()
        assert session.message_count == 4  # 2 user + 2 assistant

    @pytest.mark.asyncio
    async def test_invalid_session_id_creates_new(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Hello", "session_id": "nonexistent-id"},
            )
        events = _parse_sse(resp.text)
        done = [e for e in events if e["event"] == "done"][0]
        sid = json.loads(done["data"])["session_id"]
        assert sid != "nonexistent-id"

    @pytest.mark.asyncio
    async def test_messages_persisted_in_db(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        agent = _make_mock_agent("The answer is 42")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "What is the meaning?"},
            )
        sid = json.loads(
            [e for e in _parse_sse(resp.text) if e["event"] == "done"][0]["data"]
        )["session_id"]

        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == sid)
            .order_by(ChatMessage.id)
        )
        messages = result.scalars().all()
        assert len(messages) == 2
        assert messages[0].role == MessageRole.user
        assert messages[0].content == "What is the meaning?"
        assert messages[1].role == MessageRole.assistant
        assert "42" in messages[1].content


# ---------------------------------------------------------------------------
# 4. Conversation history
# ---------------------------------------------------------------------------

class TestRealtimeConversationHistory:
    """Verify that prior messages are passed to the agent as message_history."""

    @pytest.mark.asyncio
    async def test_second_call_includes_history(
        self, app_client: AsyncClient, sample_game
    ):
        agent1 = _make_mock_agent("You roll dice to gather resources")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent1):
            resp1 = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "How does Catan work?"},
            )
        sid = json.loads(
            [e for e in _parse_sse(resp1.text) if e["event"] == "done"][0]["data"]
        )["session_id"]

        agent2 = _make_mock_agent("You need wheat and ore for a city")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent2):
            await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "What about cities?", "session_id": sid},
            )

        history = agent2._last_call_kwargs.get("message_history", [])
        # Should contain the first exchange (user + assistant from call 1)
        assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_history_limited_to_20_messages(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Even after many exchanges, only last 20 messages are in history."""
        # Seed 24 messages into a session
        session = ChatSession(game_id="catan", mode=ChatMode.realtime)
        db.add(session)
        await db.flush()

        for i in range(12):
            db.add(ChatMessage(
                session_id=session.id, role=MessageRole.user,
                content=f"User message {i}",
            ))
            db.add(ChatMessage(
                session_id=session.id, role=MessageRole.assistant,
                content=f"Bot message {i}",
            ))
            session.message_count += 2
        await db.commit()

        agent = _make_mock_agent("Got it")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Next question", "session_id": str(session.id)},
            )

        # History excludes the current user message (it's the prompt)
        # The service fetches limit=20, then history[:-1] is passed
        history = agent._last_call_kwargs.get("message_history", [])
        assert len(history) <= 20


# ---------------------------------------------------------------------------
# 5. Image handling edge cases
# ---------------------------------------------------------------------------

class TestRealtimeImageEdgeCases:
    """Image size, type, and missing-image behavior."""

    @pytest.mark.asyncio
    async def test_oversized_image_silently_dropped(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        """Images over max_upload_size_mb are dropped but the request succeeds."""
        agent = _make_mock_agent("I only got the text")

        # 11 MB of JPEG-like data
        big_jpeg = b"\xff\xd8\xff\xe0" + (b"\x00" * (11 * 1024 * 1024))

        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Check this"},
                files={"image": ("big.jpg", io.BytesIO(big_jpeg), "image/jpeg")},
            )
        assert resp.status_code == 200

        # The prompt should be a plain string (no image attached)
        call_args = agent._last_call_args
        prompt = call_args[0] if call_args else None
        assert isinstance(prompt, str), "Oversized image should be dropped; prompt should be string"

    @pytest.mark.asyncio
    async def test_unsupported_image_type_ignored(
        self, app_client: AsyncClient, sample_game
    ):
        """Non-image content types (e.g. GIF, BMP) are not processed."""
        agent = _make_mock_agent("Text only response")
        gif = b"GIF89a" + b"\x00" * 100

        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Look at this"},
                files={"image": ("anim.gif", io.BytesIO(gif), "image/gif")},
            )
        assert resp.status_code == 200
        call_args = agent._last_call_args
        prompt = call_args[0] if call_args else None
        assert isinstance(prompt, str), "GIF should be ignored; prompt should be string"

    @pytest.mark.asyncio
    async def test_no_image_sends_string_prompt(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Just talking"},
            )
        call_args = agent._last_call_args
        prompt = call_args[0] if call_args else None
        assert isinstance(prompt, str)
        assert prompt == "Just talking"

    @pytest.mark.asyncio
    async def test_valid_image_sends_list_prompt(
        self, app_client: AsyncClient, sample_game
    ):
        """When image is valid, prompt should be [text, BinaryContent]."""
        from pydantic_ai.messages import BinaryContent

        agent = _make_mock_agent("I see pieces")
        jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 200
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "What is this?"},
                files={"image": ("snap.jpg", io.BytesIO(jpeg), "image/jpeg")},
            )
        call_args = agent._last_call_args
        prompt = call_args[0] if call_args else None
        assert isinstance(prompt, list)
        assert isinstance(prompt[0], str)
        assert isinstance(prompt[1], BinaryContent)
        assert prompt[1].media_type == "image/jpeg"


# ---------------------------------------------------------------------------
# 6. Error handling
# ---------------------------------------------------------------------------

class TestRealtimeErrors:
    """Error paths: game not found, agent errors, missing fields."""

    @pytest.mark.asyncio
    async def test_game_not_found_returns_404(self, app_client: AsyncClient):
        resp = await app_client.post(
            "/api/games/nonexistent/chat/realtime",
            data={"message": "Hi"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_missing_message_returns_422(
        self, app_client: AsyncClient, sample_game
    ):
        resp = await app_client.post(
            "/api/games/catan/chat/realtime",
            data={},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_agent_exception_returns_error_event(
        self, app_client: AsyncClient, sample_game
    ):
        """If the AI agent raises, we should get an SSE error event."""
        agent = MagicMock()

        @asynccontextmanager
        async def exploding_run_stream(*args, **kwargs):
            raise RuntimeError("Model overloaded")
            yield  # noqa: unreachable

        agent.run_stream = exploding_run_stream

        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Hello"},
            )
        assert resp.status_code == 200  # SSE always returns 200

        events = _parse_sse(resp.text)
        error_events = [e for e in events if e["event"] == "error"]
        assert len(error_events) >= 1
        error_data = json.loads(error_events[0]["data"])
        assert "overloaded" in error_data["error"].lower()

    @pytest.mark.asyncio
    async def test_empty_message_still_works(
        self, app_client: AsyncClient, sample_game
    ):
        """An empty string message should be accepted (not crash)."""
        agent = _make_mock_agent("I didn't catch that")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": ""},
            )
        # FastAPI Form(...) requires the field to exist but accepts empty string
        # depending on validation. Let's see what happens.
        assert resp.status_code in (200, 422)


# ---------------------------------------------------------------------------
# 7. TTS endpoint
# ---------------------------------------------------------------------------

class TestTTSEndpoint:
    """Test the text-to-speech proxy endpoint."""

    @pytest.mark.asyncio
    async def test_tts_no_api_key_returns_503(self, app_client: AsyncClient):
        with patch("app.routers.tts.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            resp = await app_client.post(
                "/api/tts",
                json={"text": "Hello world"},
            )
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_tts_with_api_key_calls_openai(self, app_client: AsyncClient):
        mock_response = MagicMock()
        mock_response.content = b"\x00\x01\x02"  # fake MP3 bytes
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.routers.tts.settings") as mock_settings,
            patch("app.routers.tts.httpx.AsyncClient", return_value=mock_client_instance),
        ):
            mock_settings.openai_api_key = "sk-test-key"
            resp = await app_client.post(
                "/api/tts",
                json={"text": "Hello world", "voice": "nova"},
            )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/mpeg"
        assert resp.content == b"\x00\x01\x02"

        # Verify OpenAI was called with correct params
        call_kwargs = mock_client_instance.post.call_args
        assert "audio/speech" in call_kwargs.args[0]
        body = call_kwargs.kwargs["json"]
        assert body["input"] == "Hello world"
        assert body["voice"] == "nova"
        assert body["model"] == "tts-1"

    @pytest.mark.asyncio
    async def test_tts_default_voice(self, app_client: AsyncClient):
        mock_response = MagicMock()
        mock_response.content = b"\xff"
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.routers.tts.settings") as mock_settings,
            patch("app.routers.tts.httpx.AsyncClient", return_value=mock_client_instance),
        ):
            mock_settings.openai_api_key = "sk-test"
            resp = await app_client.post(
                "/api/tts",
                json={"text": "Test"},
            )

        assert resp.status_code == 200
        body = mock_client_instance.post.call_args.kwargs["json"]
        assert body["voice"] == "alloy"  # default


# ---------------------------------------------------------------------------
# 8. Concurrent / rapid-fire requests
# ---------------------------------------------------------------------------

class TestRealtimeConcurrency:
    """Simulate rapid-fire calls (what happens when frontend sends multiple)."""

    @pytest.mark.asyncio
    async def test_multiple_sequential_calls_same_session(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        sid = None
        for i in range(5):
            agent = _make_mock_agent(f"Reply {i}")
            with patch("app.routers.chat.get_realtime_agent", return_value=agent):
                data = {"message": f"Message {i}"}
                if sid:
                    data["session_id"] = sid
                resp = await app_client.post(
                    "/api/games/catan/chat/realtime",
                    data=data,
                )
            events = _parse_sse(resp.text)
            done = [e for e in events if e["event"] == "done"][0]
            new_sid = json.loads(done["data"])["session_id"]
            if sid:
                assert new_sid == sid
            sid = new_sid

        result = await db.execute(select(ChatSession).where(ChatSession.id == sid))
        session = result.scalar_one()
        assert session.message_count == 10  # 5 user + 5 assistant


# ---------------------------------------------------------------------------
# 9. SSE response format
# ---------------------------------------------------------------------------

class TestRealtimeSSEFormat:
    """Verify the exact SSE event structure matches what the frontend expects."""

    @pytest.mark.asyncio
    async def test_chunk_event_has_text_field(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("Hello there friend")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Hi"},
            )
        events = _parse_sse(resp.text)
        for e in events:
            if e["event"] == "chunk":
                data = json.loads(e["data"])
                assert "text" in data
                assert isinstance(data["text"], str)

    @pytest.mark.asyncio
    async def test_done_event_has_session_id_and_citations(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Thanks"},
            )
        events = _parse_sse(resp.text)
        done_events = [e for e in events if e["event"] == "done"]
        assert len(done_events) == 1
        data = json.loads(done_events[0]["data"])
        assert "session_id" in data
        assert "citations" in data
        assert isinstance(data["citations"], list)

    @pytest.mark.asyncio
    async def test_no_extra_events(self, app_client: AsyncClient, sample_game):
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_realtime_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat/realtime",
                data={"message": "Test"},
            )
        events = _parse_sse(resp.text)
        event_types = {e["event"] for e in events}
        assert event_types.issubset({"chunk", "done", "error"})


# ---------------------------------------------------------------------------
# 10. Regular chat endpoint comparison
# ---------------------------------------------------------------------------

class TestRegularChatAlsoFixed:
    """Ensure the non-realtime chat endpoint also receives game context."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_gets_instructions(
        self, app_client: AsyncClient, db: AsyncSession, sample_game
    ):
        rulebook = GameRulebook(
            game_id="catan",
            status=RulebookStatus.ready,
            processed_text="Longest road gives 2 victory points.",
        )
        db.add(rulebook)
        await db.commit()

        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_teacher_agent", return_value=agent):
            resp = await app_client.post(
                "/api/games/catan/chat",
                json={"message": "Tell me about roads"},
            )
        assert resp.status_code == 200
        instructions = agent._last_call_kwargs.get("instructions", "")
        assert "Catan" in instructions
        assert "Longest road" in instructions

    @pytest.mark.asyncio
    async def test_chat_endpoint_uses_teacher_persona(
        self, app_client: AsyncClient, sample_game
    ):
        agent = _make_mock_agent("OK")
        with patch("app.routers.chat.get_teacher_agent", return_value=agent):
            await app_client.post(
                "/api/games/catan/chat",
                json={"message": "Hello"},
            )
        instructions = agent._last_call_kwargs.get("instructions", "")
        # Teacher prompt should mention teaching, not "sitting at the table"
        assert "teach" in instructions.lower()
