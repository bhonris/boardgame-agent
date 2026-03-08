"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "games",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("bgg_id", sa.Integer, nullable=True),
        sa.Column("publisher", sa.String(255), nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("min_players", sa.Integer, default=1),
        sa.Column("max_players", sa.Integer, default=4),
        sa.Column("complexity_weight", sa.Float, nullable=True),
        sa.Column("play_time_minutes", sa.Integer, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "game_rulebooks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("game_id", sa.String(100), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("source_pdf_url", sa.String(500), nullable=True),
        sa.Column("processed_text", sa.Text, nullable=True),
        sa.Column("section_structure", sa.JSON, nullable=True),
        sa.Column("status", sa.String(20), default="processing"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "rulebook_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rulebook_id", sa.String(36), sa.ForeignKey("game_rulebooks.id"), nullable=False),
        sa.Column("game_id", sa.String(100), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("section_name", sa.String(255), nullable=True),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("ix_rulebook_chunks_game_id", "rulebook_chunks", ["game_id"])

    op.create_table(
        "tutorial_scripts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("game_id", sa.String(100), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("steps", sa.JSON, nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer, nullable=True),
        sa.Column("is_curated", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "quick_references",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("game_id", sa.String(100), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("content", sa.JSON, nullable=False),
        sa.Column("display_order", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("game_id", sa.String(100), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("mode", sa.String(20), default="qa"),
        sa.Column("started_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime, nullable=True),
        sa.Column("message_count", sa.Integer, default=0),
        sa.Column("rating", sa.Integer, nullable=True),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("chat_sessions.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("rag_chunks_used", sa.JSON, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("quick_references")
    op.drop_table("tutorial_scripts")
    op.drop_table("rulebook_chunks")
    op.drop_table("game_rulebooks")
    op.drop_table("games")
