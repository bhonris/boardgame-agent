import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import ChatMessage, ChatSession, MessageRole


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(
        self, session_id: str | None, game_id: str
    ) -> ChatSession:
        if session_id:
            try:
                uid = uuid.UUID(session_id)
            except ValueError:
                uid = None
            if uid:
                result = await self.db.execute(
                    select(ChatSession).where(ChatSession.id == uid)
                )
                session = result.scalar_one_or_none()
                if session:
                    return session

        session = ChatSession(game_id=game_id)
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_conversation_history(
        self, session_id: uuid.UUID, limit: int = 20
    ) -> list[dict]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        messages.reverse()

        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    async def save_message(
        self,
        session_id: uuid.UUID,
        role: MessageRole,
        content: str,
        model_used: str | None = None,
        rag_chunks: list[dict] | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            model_used=model_used,
            rag_chunks_used=rag_chunks,
        )
        self.db.add(message)

        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one()
        session.message_count += 1

        await self.db.flush()
        return message
