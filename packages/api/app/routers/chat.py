import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.database import get_db
from app.models.base import Game, GameRulebook, MessageRole, RulebookStatus
from app.schemas.game import ChatRequest
from app.services.ai_service import teacher_agent
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
            async with teacher_agent.run_stream(
                request.message,
                message_history=[
                    {"role": m["role"], "content": m["content"]}
                    for m in history[:-1]
                ],
                model=settings.pydantic_ai_model,
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
