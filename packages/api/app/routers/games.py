import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.base import Game, QuickReference, TutorialScript
from app.schemas.game import (
    GameListResponse,
    GameSummary,
    ReferenceItem,
    ReferenceResponse,
    TutorialResponse,
    TutorialStep,
)

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("", response_model=GameListResponse)
async def list_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game).where(Game.is_active == True).order_by(Game.title)
    )
    games = result.scalars().all()
    return GameListResponse(
        games=[GameSummary.model_validate(g) for g in games]
    )


@router.get("/{game_id}", response_model=GameSummary)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameSummary.model_validate(game)


@router.get("/{game_id}/tutorial", response_model=TutorialResponse)
async def get_tutorial(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TutorialScript)
        .where(TutorialScript.game_id == game_id)
        .order_by(TutorialScript.created_at.desc())
        .limit(1)
    )
    tutorial = result.scalar_one_or_none()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found for this game")

    steps_data = tutorial.steps if isinstance(tutorial.steps, list) else tutorial.steps.get("steps", [])
    steps = [TutorialStep(**s) for s in steps_data]

    total_seconds = sum(s.estimated_seconds for s in steps)
    return TutorialResponse(
        game_id=game_id,
        steps=steps,
        total_steps=len(steps),
        estimated_minutes=max(1, total_seconds // 60),
    )


@router.get("/{game_id}/reference", response_model=ReferenceResponse)
async def get_reference(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QuickReference)
        .where(QuickReference.game_id == game_id)
        .order_by(QuickReference.display_order)
    )
    refs = result.scalars().all()
    if not refs:
        raise HTTPException(status_code=404, detail="No reference data found for this game")

    return ReferenceResponse(
        game_id=game_id,
        references=[
            ReferenceItem(
                type=r.type.value,
                title=r.content.get("title", r.type.value),
                content=r.content,
                display_order=r.display_order,
            )
            for r in refs
        ],
    )
