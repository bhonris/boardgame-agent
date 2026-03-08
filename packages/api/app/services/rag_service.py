from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import RulebookChunk
from app.services.embedding_service import get_embedding_provider


class RAGService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def retrieve(self, game_id: str, query: str, top_k: int = 5) -> list[dict]:
        embeddings = await self.embedding_provider.embed([query])
        query_embedding = embeddings[0]

        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        result = await self.db.execute(
            text("""
                SELECT id, section_name, chunk_text, chunk_index,
                       embedding <=> :embedding::vector AS distance
                FROM rulebook_chunks
                WHERE game_id = :game_id
                ORDER BY embedding <=> :embedding::vector
                LIMIT :top_k
            """),
            {"game_id": game_id, "embedding": embedding_str, "top_k": top_k},
        )
        rows = result.fetchall()

        return [
            {
                "id": str(row.id),
                "section_name": row.section_name,
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "distance": row.distance,
            }
            for row in rows
        ]

    async def build_context(self, game_id: str, query: str, top_k: int = 5) -> str:
        chunks = await self.retrieve(game_id, query, top_k)
        if not chunks:
            return "No relevant rulebook content found."

        context_parts = []
        for chunk in chunks:
            section = chunk.get("section_name", "Unknown Section")
            context_parts.append(f"[{section}]\n{chunk['chunk_text']}")

        return "\n\n---\n\n".join(context_parts)
