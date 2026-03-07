import uuid

import pymupdf
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import GameRulebook, RulebookStatus


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text() + "\n\n"
    doc.close()
    return text


def detect_sections(text: str) -> list[dict]:
    lines = text.split("\n")
    sections = []
    current_section = {"name": "Introduction", "content": ""}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_section["content"] += "\n"
            continue

        is_heading = (
            stripped.isupper()
            and len(stripped) > 3
            and len(stripped) < 100
        ) or (
            len(stripped) < 80
            and not stripped.endswith(".")
            and stripped[0].isupper()
            and len(stripped.split()) <= 8
            and current_section["content"].strip().endswith("\n")
        )

        if is_heading:
            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {"name": stripped, "content": ""}
        else:
            current_section["content"] += line + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    return sections


def chunk_text(text: str, section_name: str, max_tokens: int = 500) -> list[dict]:
    words = text.split()
    chunks = []
    chunk_index = 0

    for i in range(0, len(words), max_tokens):
        chunk_words = words[i : i + max_tokens]
        chunk_text = " ".join(chunk_words)
        if chunk_text.strip():
            chunks.append({
                "section_name": section_name,
                "chunk_text": chunk_text,
                "chunk_index": chunk_index,
                "token_count": len(chunk_words),
            })
            chunk_index += 1

    return chunks


async def ingest_rulebook(
    db: AsyncSession,
    game_id: str,
    pdf_bytes: bytes,
    version: str = "1.0",
) -> uuid.UUID:
    rulebook = GameRulebook(
        game_id=game_id,
        version=version,
        status=RulebookStatus.processing,
    )
    db.add(rulebook)
    await db.flush()
    rulebook_id = rulebook.id

    try:
        full_text = extract_text_from_pdf(pdf_bytes)
        rulebook.processed_text = full_text

        sections = detect_sections(full_text)
        section_names = [s["name"] for s in sections]
        rulebook.section_structure = {"sections": section_names}

        rulebook.status = RulebookStatus.ready
        await db.commit()
    except Exception:
        rulebook.status = RulebookStatus.error
        await db.commit()
        raise

    return rulebook_id
