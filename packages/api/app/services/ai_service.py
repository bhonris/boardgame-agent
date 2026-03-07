from dataclasses import dataclass

from pydantic import BaseModel
from pydantic_ai import Agent

from app.config import settings


class TeachingResponse(BaseModel):
    text: str
    citations: list[dict] = []


@dataclass
class TeacherDeps:
    game_id: str
    game_title: str
    rulebook_context: str


TEACHER_SYSTEM_PROMPT = """You are an expert board game teacher at a board game cafe.
Your job is to help customers learn and play board games.

Key principles:
- Teach the minimum needed to start playing, then introduce rules as they become relevant
- Use simple, friendly language — avoid jargon
- When citing rules, reference the section or page from the rulebook
- If you're unsure about a rule, say so honestly
- Keep answers concise but complete

You are currently teaching: {game_title}

Relevant rulebook content:
{rulebook_context}
"""

teacher_agent = Agent(
    settings.pydantic_ai_model,
    system_prompt=TEACHER_SYSTEM_PROMPT,
    result_type=str,
)


@dataclass
class VisionDeps:
    game_id: str
    game_title: str
    mode: str


class VisionResult(BaseModel):
    analysis: str
    confidence: str
    related_rules: list[str] = []


VISION_SYSTEM_PROMPT = """You are an expert board game teacher with visual analysis capabilities.
You are helping a customer identify and understand game components for: {game_title}

Mode: {mode}
- "identify": Identify the game component in the image and explain what it does
- "read_card": Read the text on a card and explain its effects
- "verify_setup": Check if the board/game setup matches the correct initial setup

Provide clear, helpful explanations. If you can't identify something with confidence, say so.
"""

vision_agent = Agent(
    settings.vision_model,
    system_prompt=VISION_SYSTEM_PROMPT,
    result_type=str,
)
