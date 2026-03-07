import pytest

from app.schemas.game import (
    ChatRequest,
    GameListResponse,
    GameSummary,
    ReferenceItem,
    ReferenceResponse,
    TTSRequest,
    TutorialResponse,
    TutorialStep,
    VisionRequest,
    VisionResponse,
)


class TestGameSummary:
    def test_create_game_summary(self):
        game = GameSummary(
            id="catan",
            title="Catan",
            cover_image_url="/images/catan.jpg",
            min_players=3,
            max_players=4,
            complexity_weight=2.3,
            play_time_minutes=90,
            description="A trading game",
        )
        assert game.id == "catan"
        assert game.title == "Catan"
        assert game.min_players == 3

    def test_game_summary_nullable_fields(self):
        game = GameSummary(
            id="test",
            title="Test",
            cover_image_url=None,
            min_players=2,
            max_players=4,
            complexity_weight=None,
            play_time_minutes=None,
            description=None,
        )
        assert game.cover_image_url is None
        assert game.complexity_weight is None


class TestGameListResponse:
    def test_empty_list(self):
        response = GameListResponse(games=[])
        assert response.games == []

    def test_with_games(self):
        games = [
            GameSummary(
                id="catan", title="Catan", cover_image_url=None,
                min_players=3, max_players=4, complexity_weight=2.3,
                play_time_minutes=90, description="Test",
            ),
        ]
        response = GameListResponse(games=games)
        assert len(response.games) == 1


class TestTutorialStep:
    def test_create_step(self):
        step = TutorialStep(
            id=1,
            phase="theme_and_goal",
            title="What is Catan?",
            content="You're settlers...",
            estimated_seconds=30,
        )
        assert step.id == 1
        assert step.phase == "theme_and_goal"
        assert step.image_url is None

    def test_step_with_image(self):
        step = TutorialStep(
            id=2,
            phase="components",
            title="Components",
            content="...",
            image_url="/images/catan/components.jpg",
            estimated_seconds=60,
        )
        assert step.image_url == "/images/catan/components.jpg"


class TestTutorialResponse:
    def test_create_response(self):
        response = TutorialResponse(
            game_id="catan",
            steps=[
                TutorialStep(id=1, phase="theme_and_goal", title="What?", content="...", estimated_seconds=30),
            ],
            total_steps=1,
            estimated_minutes=1,
        )
        assert response.game_id == "catan"
        assert response.total_steps == 1


class TestChatRequest:
    def test_create_request(self):
        req = ChatRequest(message="Can I trade?")
        assert req.message == "Can I trade?"
        assert req.session_id is None

    def test_with_session_id(self):
        req = ChatRequest(session_id="abc-123", message="How do I build?")
        assert req.session_id == "abc-123"


class TestVisionRequest:
    def test_defaults(self):
        req = VisionRequest()
        assert req.mode == "identify"
        assert req.session_id is None


class TestVisionResponse:
    def test_create_response(self):
        resp = VisionResponse(
            analysis="This is a settlement",
            confidence="high",
            related_rules=["Settlements cost 1 brick..."],
        )
        assert resp.confidence == "high"
        assert len(resp.related_rules) == 1


class TestReferenceResponse:
    def test_create_response(self):
        resp = ReferenceResponse(
            game_id="catan",
            references=[
                ReferenceItem(
                    type="turn_order",
                    title="Turn Structure",
                    content={"items": ["Roll dice", "Trade", "Build"]},
                    display_order=0,
                ),
            ],
        )
        assert len(resp.references) == 1
        assert resp.references[0].type == "turn_order"


class TestTTSRequest:
    def test_defaults(self):
        req = TTSRequest(text="Hello world")
        assert req.voice == "alloy"

    def test_custom_voice(self):
        req = TTSRequest(text="Hello", voice="nova")
        assert req.voice == "nova"
