"""Tests for database queries used across routers and services."""
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import (
    Base,
    ChatMessage,
    ChatMode,
    ChatSession,
    Game,
    GameRulebook,
    MessageRole,
    QuickReference,
    ReferenceType,
    RulebookChunk,
    RulebookStatus,
    TutorialScript,
)
from app.services.session_service import SessionService


# ── Game queries (used in routers/games.py and routers/chat.py) ──


class TestGameQueries:
    @pytest.mark.asyncio
    async def test_list_active_games(self, db: AsyncSession, sample_games):
        result = await db.execute(
            select(Game).where(Game.is_active == True).order_by(Game.title)
        )
        games = result.scalars().all()
        titles = [g.title for g in games]
        assert titles == ["Catan", "Wingspan"]
        assert "Inactive Game" not in titles

    @pytest.mark.asyncio
    async def test_list_games_empty(self, db: AsyncSession):
        result = await db.execute(
            select(Game).where(Game.is_active == True).order_by(Game.title)
        )
        games = result.scalars().all()
        assert games == []

    @pytest.mark.asyncio
    async def test_get_game_by_id(self, db: AsyncSession, sample_game):
        result = await db.execute(select(Game).where(Game.id == "catan"))
        game = result.scalar_one_or_none()
        assert game is not None
        assert game.title == "Catan"
        assert game.min_players == 3
        assert game.max_players == 4

    @pytest.mark.asyncio
    async def test_get_game_not_found(self, db: AsyncSession):
        result = await db.execute(select(Game).where(Game.id == "nonexistent"))
        game = result.scalar_one_or_none()
        assert game is None

    @pytest.mark.asyncio
    async def test_game_all_fields(self, db: AsyncSession, sample_game):
        result = await db.execute(select(Game).where(Game.id == "catan"))
        game = result.scalar_one()
        assert game.complexity_weight == 2.3
        assert game.play_time_minutes == 90
        assert game.description == "Trade and build"
        assert game.cover_image_url == "/images/catan.jpg"
        assert game.is_active is True
        assert game.created_at is not None

    @pytest.mark.asyncio
    async def test_game_nullable_fields(self, db: AsyncSession):
        game = Game(id="minimal", title="Minimal Game")
        db.add(game)
        await db.commit()
        result = await db.execute(select(Game).where(Game.id == "minimal"))
        g = result.scalar_one()
        assert g.bgg_id is None
        assert g.publisher is None
        assert g.year is None
        assert g.complexity_weight is None
        assert g.description is None


# ── Tutorial queries (used in routers/games.py) ──


class TestTutorialQueries:
    @pytest.mark.asyncio
    async def test_get_latest_tutorial(self, db: AsyncSession, sample_tutorial):
        result = await db.execute(
            select(TutorialScript)
            .where(TutorialScript.game_id == "catan")
            .order_by(TutorialScript.created_at.desc())
            .limit(1)
        )
        tutorial = result.scalar_one_or_none()
        assert tutorial is not None
        assert tutorial.game_id == "catan"
        assert len(tutorial.steps) == 2

    @pytest.mark.asyncio
    async def test_tutorial_steps_json(self, db: AsyncSession, sample_tutorial):
        result = await db.execute(
            select(TutorialScript).where(TutorialScript.game_id == "catan")
        )
        tutorial = result.scalar_one()
        steps = tutorial.steps
        assert steps[0]["phase"] == "theme_and_goal"
        assert steps[1]["title"] == "Components"
        assert steps[0]["estimated_seconds"] == 30

    @pytest.mark.asyncio
    async def test_tutorial_not_found(self, db: AsyncSession, sample_game):
        result = await db.execute(
            select(TutorialScript).where(TutorialScript.game_id == "catan")
        )
        tutorial = result.scalar_one_or_none()
        assert tutorial is None

    @pytest.mark.asyncio
    async def test_multiple_tutorials_returns_latest(self, db: AsyncSession, sample_game):
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        t1 = TutorialScript(
            game_id="catan", version="1.0",
            steps=[{"id": 1, "phase": "old", "title": "Old", "content": "old", "estimated_seconds": 10}],
            created_at=now - timedelta(hours=1),
        )
        db.add(t1)
        t2 = TutorialScript(
            game_id="catan", version="2.0",
            steps=[{"id": 1, "phase": "new", "title": "New", "content": "new", "estimated_seconds": 20}],
            created_at=now,
        )
        db.add(t2)
        await db.commit()

        result = await db.execute(
            select(TutorialScript)
            .where(TutorialScript.game_id == "catan")
            .order_by(TutorialScript.created_at.desc())
            .limit(1)
        )
        latest = result.scalar_one()
        assert latest.version == "2.0"


# ── QuickReference queries (used in routers/games.py) ──


class TestReferenceQueries:
    @pytest.mark.asyncio
    async def test_get_references_ordered(self, db: AsyncSession, sample_references):
        result = await db.execute(
            select(QuickReference)
            .where(QuickReference.game_id == "catan")
            .order_by(QuickReference.display_order)
        )
        refs = result.scalars().all()
        assert len(refs) == 2
        assert refs[0].type == ReferenceType.turn_order
        assert refs[1].type == ReferenceType.scoring
        assert refs[0].display_order < refs[1].display_order

    @pytest.mark.asyncio
    async def test_reference_json_content(self, db: AsyncSession, sample_references):
        result = await db.execute(
            select(QuickReference)
            .where(QuickReference.game_id == "catan", QuickReference.type == ReferenceType.turn_order)
        )
        ref = result.scalar_one()
        assert ref.content["title"] == "Turn Structure"
        assert "Roll dice" in ref.content["items"]

    @pytest.mark.asyncio
    async def test_references_not_found(self, db: AsyncSession, sample_game):
        result = await db.execute(
            select(QuickReference).where(QuickReference.game_id == "catan")
        )
        refs = result.scalars().all()
        assert refs == []


# ── Rulebook queries (used in routers/chat.py) ──


class TestRulebookQueries:
    @pytest.mark.asyncio
    async def test_get_ready_rulebook(self, db: AsyncSession, sample_rulebook):
        result = await db.execute(
            select(GameRulebook).where(
                GameRulebook.game_id == "catan",
                GameRulebook.status == RulebookStatus.ready,
            ).order_by(GameRulebook.created_at.desc()).limit(1)
        )
        rulebook = result.scalar_one_or_none()
        assert rulebook is not None
        assert "trading resources" in rulebook.processed_text

    @pytest.mark.asyncio
    async def test_no_ready_rulebook(self, db: AsyncSession, sample_game):
        rb = GameRulebook(
            game_id="catan", status=RulebookStatus.processing, processed_text=None
        )
        db.add(rb)
        await db.commit()

        result = await db.execute(
            select(GameRulebook).where(
                GameRulebook.game_id == "catan",
                GameRulebook.status == RulebookStatus.ready,
            )
        )
        rulebook = result.scalar_one_or_none()
        assert rulebook is None

    @pytest.mark.asyncio
    async def test_rulebook_with_chunks(self, db: AsyncSession, sample_rulebook):
        chunk = RulebookChunk(
            rulebook_id=sample_rulebook.id,
            game_id="catan",
            section_name="Setup",
            chunk_text="Place the board in the center.",
            chunk_index=0,
            token_count=6,
        )
        db.add(chunk)
        await db.commit()

        result = await db.execute(
            select(RulebookChunk).where(RulebookChunk.rulebook_id == sample_rulebook.id)
        )
        chunks = result.scalars().all()
        assert len(chunks) == 1
        assert chunks[0].section_name == "Setup"
        assert chunks[0].chunk_index == 0


# ── SessionService queries (used in routers/chat.py) ──


class TestSessionService:
    @pytest.mark.asyncio
    async def test_create_new_session(self, db: AsyncSession, sample_game):
        svc = SessionService(db)
        session = await svc.get_or_create_session(None, "catan")
        assert session.game_id == "catan"
        assert session.id is not None
        assert session.mode == ChatMode.qa

    @pytest.mark.asyncio
    async def test_get_existing_session(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        session = await svc.get_or_create_session(sample_session.id, "catan")
        assert session.id == sample_session.id

    @pytest.mark.asyncio
    async def test_invalid_session_id_creates_new(self, db: AsyncSession, sample_game):
        svc = SessionService(db)
        session = await svc.get_or_create_session("not-a-real-id", "catan")
        assert session.game_id == "catan"
        assert session.id != "not-a-real-id"

    @pytest.mark.asyncio
    async def test_save_message(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        msg = await svc.save_message(
            sample_session.id, MessageRole.user, "How do I build a settlement?"
        )
        assert msg.content == "How do I build a settlement?"
        assert msg.role == MessageRole.user
        assert msg.session_id == sample_session.id

    @pytest.mark.asyncio
    async def test_save_message_increments_count(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        assert sample_session.message_count == 0
        await svc.save_message(sample_session.id, MessageRole.user, "Hello")
        await db.refresh(sample_session)
        assert sample_session.message_count == 1
        await svc.save_message(sample_session.id, MessageRole.assistant, "Hi!")
        await db.refresh(sample_session)
        assert sample_session.message_count == 2

    @pytest.mark.asyncio
    async def test_save_message_with_model_info(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        msg = await svc.save_message(
            sample_session.id, MessageRole.assistant, "Answer",
            model_used="openai:gpt-5-nano",
            rag_chunks=[ {"chunk_id": "abc", "score": 0.9}],
        )
        assert msg.model_used == "openai:gpt-5-nano"
        assert msg.rag_chunks_used[0]["chunk_id"] == "abc"

    @pytest.mark.asyncio
    async def test_conversation_history_order(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        await svc.save_message(sample_session.id, MessageRole.user, "First")
        await svc.save_message(sample_session.id, MessageRole.assistant, "Second")
        await svc.save_message(sample_session.id, MessageRole.user, "Third")

        history = await svc.get_conversation_history(sample_session.id)
        assert len(history) == 3
        assert history[0]["content"] == "First"
        assert history[1]["content"] == "Second"
        assert history[2]["content"] == "Third"

    @pytest.mark.asyncio
    async def test_conversation_history_limit(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        for i in range(5):
            await svc.save_message(sample_session.id, MessageRole.user, f"Message {i}")

        history = await svc.get_conversation_history(sample_session.id, limit=3)
        assert len(history) == 3
        assert history[0]["content"] == "Message 2"
        assert history[2]["content"] == "Message 4"

    @pytest.mark.asyncio
    async def test_conversation_history_roles(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        await svc.save_message(sample_session.id, MessageRole.user, "Question")
        await svc.save_message(sample_session.id, MessageRole.assistant, "Answer")
        history = await svc.get_conversation_history(sample_session.id)
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_empty_conversation_history(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        history = await svc.get_conversation_history(sample_session.id)
        assert history == []


# ── Model relationship tests ──


class TestModelRelationships:
    @pytest.mark.asyncio
    async def test_game_has_rulebooks(self, db: AsyncSession, sample_rulebook):
        result = await db.execute(select(Game).where(Game.id == "catan"))
        game = result.scalar_one()
        await db.refresh(game, ["rulebooks"])
        assert len(game.rulebooks) == 1
        assert game.rulebooks[0].version == "1.0"

    @pytest.mark.asyncio
    async def test_game_has_tutorials(self, db: AsyncSession, sample_tutorial):
        result = await db.execute(select(Game).where(Game.id == "catan"))
        game = result.scalar_one()
        await db.refresh(game, ["tutorials"])
        assert len(game.tutorials) == 1

    @pytest.mark.asyncio
    async def test_game_has_references(self, db: AsyncSession, sample_references):
        result = await db.execute(select(Game).where(Game.id == "catan"))
        game = result.scalar_one()
        await db.refresh(game, ["references"])
        assert len(game.references) == 2

    @pytest.mark.asyncio
    async def test_session_has_messages(self, db: AsyncSession, sample_session):
        svc = SessionService(db)
        await svc.save_message(sample_session.id, MessageRole.user, "Hello")
        await svc.save_message(sample_session.id, MessageRole.assistant, "Hi")

        result = await db.execute(
            select(ChatSession).where(ChatSession.id == sample_session.id)
        )
        session = result.scalar_one()
        await db.refresh(session, ["messages"])
        assert len(session.messages) == 2

    @pytest.mark.asyncio
    async def test_rulebook_has_chunks(self, db: AsyncSession, sample_rulebook):
        chunk = RulebookChunk(
            rulebook_id=sample_rulebook.id,
            game_id="catan",
            chunk_text="Chunk 1",
            chunk_index=0,
        )
        db.add(chunk)
        await db.commit()
        await db.refresh(sample_rulebook, ["chunks"])
        assert len(sample_rulebook.chunks) == 1


# ── Seed data pattern tests ──


class TestSeedDataPatterns:
    """Test the query patterns used in seed_data.py for idempotent inserts."""

    @pytest.mark.asyncio
    async def test_upsert_game_idempotent(self, db: AsyncSession):
        game = Game(id="catan", title="Catan", min_players=3, max_players=4)
        db.add(game)
        await db.commit()

        result = await db.execute(select(Game).where(Game.id == "catan"))
        existing = result.scalar_one_or_none()
        assert existing is not None

        # Second insert should be skipped (seed pattern)
        if not existing:
            db.add(Game(id="catan", title="Catan v2"))
        await db.commit()

        result = await db.execute(select(Game).where(Game.id == "catan"))
        game = result.scalar_one()
        assert game.title == "Catan"

    @pytest.mark.asyncio
    async def test_reference_lookup_by_type(self, db: AsyncSession, sample_game):
        ref = QuickReference(
            game_id="catan", type=ReferenceType.turn_order,
            content={"title": "Turns"}, display_order=0,
        )
        db.add(ref)
        await db.commit()

        result = await db.execute(
            select(QuickReference).where(
                QuickReference.game_id == "catan",
                QuickReference.type == ReferenceType.turn_order,
            )
        )
        existing = result.scalar_one_or_none()
        assert existing is not None
        assert existing.content["title"] == "Turns"
