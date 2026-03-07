import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RulebookStatus(str, enum.Enum):
    processing = "processing"
    ready = "ready"
    error = "error"


class ReferenceType(str, enum.Enum):
    turn_order = "turn_order"
    icons = "icons"
    scoring = "scoring"
    setup = "setup"


class ChatMode(str, enum.Enum):
    tutorial = "tutorial"
    qa = "qa"
    dispute = "dispute"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    bgg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_players: Mapped[int] = mapped_column(Integer, default=1)
    max_players: Mapped[int] = mapped_column(Integer, default=4)
    complexity_weight: Mapped[float | None] = mapped_column(nullable=True)
    play_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    rulebooks: Mapped[list["GameRulebook"]] = relationship(back_populates="game")
    tutorials: Mapped[list["TutorialScript"]] = relationship(back_populates="game")
    references: Mapped[list["QuickReference"]] = relationship(back_populates="game")


class GameRulebook(Base):
    __tablename__ = "game_rulebooks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    section_structure: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[RulebookStatus] = mapped_column(
        Enum(RulebookStatus), default=RulebookStatus.processing
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    game: Mapped["Game"] = relationship(back_populates="rulebooks")
    chunks: Mapped[list["RulebookChunk"]] = relationship(back_populates="rulebook")


class RulebookChunk(Base):
    __tablename__ = "rulebook_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rulebook_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("game_rulebooks.id"), nullable=False)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)
    section_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    rulebook: Mapped["GameRulebook"] = relationship(back_populates="chunks")


class TutorialScript(Base):
    __tablename__ = "tutorial_scripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    steps: Mapped[dict] = mapped_column(JSONB, nullable=False)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_curated: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    game: Mapped["Game"] = relationship(back_populates="tutorials")


class QuickReference(Base):
    __tablename__ = "quick_references"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)
    type: Mapped[ReferenceType] = mapped_column(Enum(ReferenceType), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    game: Mapped["Game"] = relationship(back_populates="references")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[ChatMode] = mapped_column(Enum(ChatMode), default=ChatMode.qa)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rag_chunks_used: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
