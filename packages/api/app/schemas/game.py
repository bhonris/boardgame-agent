from pydantic import BaseModel


class GameSummary(BaseModel):
    id: str
    title: str
    cover_image_url: str | None
    min_players: int
    max_players: int
    complexity_weight: float | None
    play_time_minutes: int | None
    description: str | None

    model_config = {"from_attributes": True}


class GameListResponse(BaseModel):
    games: list[GameSummary]


class TutorialStep(BaseModel):
    id: int
    phase: str
    title: str
    content: str
    image_url: str | None = None
    estimated_seconds: int = 60


class TutorialResponse(BaseModel):
    game_id: str
    steps: list[TutorialStep]
    total_steps: int
    estimated_minutes: int


class ReferenceItem(BaseModel):
    type: str
    title: str
    content: dict
    display_order: int


class ReferenceResponse(BaseModel):
    game_id: str
    references: list[ReferenceItem]


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatChunk(BaseModel):
    text: str


class ChatDone(BaseModel):
    citations: list[dict] = []
    session_id: str


class VisionRequest(BaseModel):
    mode: str = "identify"
    session_id: str | None = None


class VisionResponse(BaseModel):
    analysis: str
    confidence: str
    related_rules: list[str] = []


class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"
