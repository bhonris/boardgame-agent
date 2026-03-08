import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import (
    Base,
    ChatMode,
    ChatSession,
    Game,
    GameRulebook,
    MessageRole,
    QuickReference,
    ReferenceType,
    RulebookStatus,
    TutorialScript,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(async_engine) -> AsyncSession:
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def app_client(async_engine):
    """FastAPI test client with overridden DB dependency."""
    from app.database import get_db
    from main import app

    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_game(db: AsyncSession) -> Game:
    game = Game(
        id="catan",
        title="Catan",
        min_players=3,
        max_players=4,
        complexity_weight=2.3,
        play_time_minutes=90,
        description="Trade and build",
        cover_image_url="/images/catan.jpg",
    )
    db.add(game)
    await db.commit()
    return game


@pytest_asyncio.fixture
async def sample_games(db: AsyncSession) -> list[Game]:
    games = [
        Game(id="catan", title="Catan", min_players=3, max_players=4),
        Game(id="wingspan", title="Wingspan", min_players=1, max_players=5),
        Game(id="inactive", title="Inactive Game", min_players=2, max_players=2, is_active=False),
    ]
    for g in games:
        db.add(g)
    await db.commit()
    return games


@pytest_asyncio.fixture
async def sample_tutorial(db: AsyncSession, sample_game: Game) -> TutorialScript:
    tutorial = TutorialScript(
        game_id=sample_game.id,
        version="1.0",
        steps=[
            {"id": 1, "phase": "theme_and_goal", "title": "What is Catan?", "content": "You settle an island.", "estimated_seconds": 30},
            {"id": 2, "phase": "components", "title": "Components", "content": "Tiles, cards, pieces.", "estimated_seconds": 45},
        ],
        estimated_duration_minutes=2,
    )
    db.add(tutorial)
    await db.commit()
    return tutorial


@pytest_asyncio.fixture
async def sample_references(db: AsyncSession, sample_game: Game) -> list[QuickReference]:
    refs = [
        QuickReference(
            game_id=sample_game.id,
            type=ReferenceType.turn_order,
            content={"title": "Turn Structure", "items": ["Roll dice", "Trade", "Build"]},
            display_order=0,
        ),
        QuickReference(
            game_id=sample_game.id,
            type=ReferenceType.scoring,
            content={"title": "Scoring", "items": ["Settlement=1VP", "City=2VP"]},
            display_order=1,
        ),
    ]
    for r in refs:
        db.add(r)
    await db.commit()
    return refs


@pytest_asyncio.fixture
async def sample_rulebook(db: AsyncSession, sample_game: Game) -> GameRulebook:
    rulebook = GameRulebook(
        game_id=sample_game.id,
        version="1.0",
        processed_text="Catan is a game about trading resources and building settlements.",
        status=RulebookStatus.ready,
    )
    db.add(rulebook)
    await db.commit()
    return rulebook


@pytest_asyncio.fixture
async def sample_session(db: AsyncSession, sample_game: Game) -> ChatSession:
    session = ChatSession(game_id=sample_game.id, mode=ChatMode.qa)
    db.add(session)
    await db.commit()
    return session
