from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic_ai.messages import BinaryContent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.base import Game
from app.schemas.game import VisionResponse
from app.services.ai_service import VisionDeps, get_vision_agent

router = APIRouter(prefix="/api/games", tags=["vision"])


@router.post("/{game_id}/vision", response_model=VisionResponse)
async def analyze_image(
    game_id: str,
    image: UploadFile = File(...),
    mode: str = Form("identify"),
    session_id: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if mode not in ("identify", "read_card", "verify_setup"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Unsupported image type")

    contents = await image.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail=f"Image too large (max {settings.max_upload_size_mb}MB)")

    mode_prompts = {
        "identify": f"Identify this game component from {game.title} and explain what it is and how it's used in the game.",
        "read_card": f"Read the text on this card from {game.title} and explain what it does, including any game effects.",
        "verify_setup": f"Check if this setup for {game.title} looks correct. Point out any issues or missing pieces.",
    }

    prompt = mode_prompts[mode]

    try:
        result = await get_vision_agent().run(
            [
                prompt,
                BinaryContent(data=contents, media_type=image.content_type),
            ],
            model=settings.vision_model,
        )

        response_text = result.data if isinstance(result.data, str) else str(result.data)

        return VisionResponse(
            analysis=response_text,
            confidence="high",
            related_rules=[],
        )
    except Exception as e:
        return VisionResponse(
            analysis=f"I wasn't able to analyze this image clearly. Try taking a photo with better lighting or from a different angle. Error: {str(e)}",
            confidence="low",
            related_rules=[],
        )
