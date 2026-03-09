import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from pydantic_ai.messages import BinaryContent, ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.config import settings
from app.database import get_db
from app.models.base import ChatMode, Game, GameRulebook, MessageRole, RulebookStatus
from app.schemas.game import ChatRequest
from app.services.ai_service import (
    format_realtime_prompt,
    format_teacher_prompt,
    get_realtime_agent,
    get_teacher_agent,
)
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/games", tags=["chat"])


async def _get_rulebook_text(db: AsyncSession, game_id: str) -> str:
    result = await db.execute(
        select(GameRulebook).where(
            GameRulebook.game_id == game_id,
            GameRulebook.status == RulebookStatus.ready,
        ).order_by(GameRulebook.created_at.desc()).limit(1)
    )
    rulebook = result.scalar_one_or_none()
    if rulebook and rulebook.processed_text:
        return rulebook.processed_text
    return "No rulebook content available. Answer based on your general knowledge of this game."


@router.post("/{game_id}/chat")
async def chat(game_id: str, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    session_service = SessionService(db)
    session = await session_service.get_or_create_session(request.session_id, game_id)

    await session_service.save_message(session.id, MessageRole.user, request.message)

    rulebook_text = await _get_rulebook_text(db, game_id)
    history = await session_service.get_conversation_history(session.id)

    async def event_stream() -> AsyncIterator[dict]:
        full_response = ""
        try:
            message_history = []
            for m in history[:-1]:
                if m["role"] == "user":
                    message_history.append(ModelRequest(parts=[UserPromptPart(content=m["content"])]))
                else:
                    message_history.append(ModelResponse(parts=[TextPart(content=m["content"])]))

            instructions = format_teacher_prompt(game.title, rulebook_text)
            async with get_teacher_agent().run_stream(
                request.message,
                message_history=message_history,
                model=settings.pydantic_ai_model,
                instructions=instructions,
            ) as result:
                async for chunk in result.stream_text(delta=True):
                    full_response += chunk
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"text": chunk}),
                    }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }
            return

        await session_service.save_message(
            session.id,
            MessageRole.assistant,
            full_response,
            model_used=settings.pydantic_ai_model,
        )
        await db.commit()

        yield {
            "event": "done",
            "data": json.dumps({
                "citations": [],
                "session_id": str(session.id),
            }),
        }

    return EventSourceResponse(event_stream())


@router.post("/{game_id}/chat/realtime")
async def chat_realtime(
    game_id: str,
    message: str = Form(...),
    image: UploadFile | None = File(None),
    session_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    session_service = SessionService(db)
    session = await session_service.get_or_create_session(
        session_id, game_id, mode=ChatMode.realtime,
    )

    await session_service.save_message(session.id, MessageRole.user, message)

    rulebook_text = await _get_rulebook_text(db, game_id)
    history = await session_service.get_conversation_history(session.id)

    # Process image if provided
    image_content = None
    if image and image.content_type in ("image/jpeg", "image/png", "image/webp"):
        contents = await image.read()
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(contents) <= max_bytes:
            image_content = BinaryContent(data=contents, media_type=image.content_type)

    async def event_stream() -> AsyncIterator[dict]:
        full_response = ""
        try:
            message_history = []
            for m in history[:-1]:
                if m["role"] == "user":
                    message_history.append(ModelRequest(parts=[UserPromptPart(content=m["content"])]))
                else:
                    message_history.append(ModelResponse(parts=[TextPart(content=m["content"])]))

            # Build prompt with optional image context
            if image_content:
                prompt = [
                    "The player is showing you the current board state in the attached image. "
                    "Use it to answer their question.\n\n"
                    f"Player: {message}",
                    image_content,
                ]
            else:
                prompt = message

            instructions = format_realtime_prompt(game.title, rulebook_text)
            async with get_realtime_agent().run_stream(
                prompt,
                message_history=message_history,
                model=settings.realtime_model,
                instructions=instructions,
            ) as result:
                async for chunk in result.stream_text(delta=True):
                    full_response += chunk
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"text": chunk}),
                    }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }
            return

        await session_service.save_message(
            session.id,
            MessageRole.assistant,
            full_response,
            model_used=settings.realtime_model,
        )
        await db.commit()

        yield {
            "event": "done",
            "data": json.dumps({
                "citations": [],
                "session_id": str(session.id),
            }),
        }

    return EventSourceResponse(event_stream())
