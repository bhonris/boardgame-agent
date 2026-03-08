"""Seed the database with demo games, tutorials, and quick references."""
import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, engine
from app.models.base import Base, Game, QuickReference, ReferenceType, TutorialScript

GAMES = [
    {
        "id": "catan",
        "title": "Catan",
        "min_players": 3,
        "max_players": 4,
        "complexity_weight": 2.3,
        "play_time_minutes": 90,
        "description": "Trade, build, and settle the island of Catan. Collect resources, trade with other players, and build roads, settlements, and cities to earn victory points.",
        "cover_image_url": "/images/catan.jpg",
        "publisher": "Catan Studio",
        "year": 1995,
    },
    {
        "id": "ticket-to-ride",
        "title": "Ticket to Ride",
        "min_players": 2,
        "max_players": 5,
        "complexity_weight": 1.9,
        "play_time_minutes": 60,
        "description": "Build train routes across North America to connect cities and complete destination tickets. Collect cards, claim routes, and build the longest railroad!",
        "cover_image_url": "/images/ticket-to-ride.jpg",
        "publisher": "Days of Wonder",
        "year": 2004,
    },
    {
        "id": "wingspan",
        "title": "Wingspan",
        "min_players": 1,
        "max_players": 5,
        "complexity_weight": 2.4,
        "play_time_minutes": 70,
        "description": "Attract birds to your wildlife preserves in this engine-building game. Each bird has unique powers that chain together for increasingly powerful turns.",
        "cover_image_url": "/images/wingspan.jpg",
        "publisher": "Stonemaier Games",
        "year": 2019,
    },
    {
        "id": "splendor",
        "title": "Splendor",
        "min_players": 2,
        "max_players": 4,
        "complexity_weight": 1.8,
        "play_time_minutes": 30,
        "description": "Collect gem tokens, purchase development cards, and attract nobles to earn prestige points. A fast-paced engine-building game where your gem cards give permanent discounts on future purchases.",
        "cover_image_url": "/images/splendor.jpg",
        "publisher": "Space Cowboys",
        "year": 2014,
    },
]

QUICK_REFERENCES = {
    "catan": [
        {
            "type": "turn_order",
            "content": {
                "title": "Turn Structure",
                "items": [
                    "1. Roll both dice (everyone collects resources)",
                    "2. Trade with players or bank (4:1, or better with ports)",
                    "3. Build: roads, settlements, cities, or development cards"
                ]
            },
            "display_order": 0,
        },
        {
            "type": "icons",
            "content": {
                "title": "Building Costs",
                "items": [
                    "Road: 1 Brick + 1 Lumber",
                    "Settlement: 1 Brick + 1 Lumber + 1 Grain + 1 Wool (1 VP)",
                    "City: 3 Ore + 2 Grain (2 VP)",
                    "Dev Card: 1 Ore + 1 Grain + 1 Wool"
                ]
            },
            "display_order": 1,
        },
        {
            "type": "scoring",
            "content": {
                "title": "Victory Points (Goal: 10)",
                "items": [
                    "Settlement = 1 VP",
                    "City = 2 VP",
                    "Longest Road (5+) = 2 VP",
                    "Largest Army (3+ Knights) = 2 VP",
                    "VP Development Cards = 1 VP each"
                ]
            },
            "display_order": 2,
        },
    ],
    "ticket-to-ride": [
        {
            "type": "turn_order",
            "content": {
                "title": "Turn Actions (pick one)",
                "items": [
                    "1. Draw 2 Train Cards (face-up locomotive = only 1 card)",
                    "2. Claim a Route (play matching color cards)",
                    "3. Draw 3 Destination Tickets (keep at least 1)"
                ]
            },
            "display_order": 0,
        },
        {
            "type": "scoring",
            "content": {
                "title": "Route Points",
                "items": [
                    "1 car = 1 pt | 2 cars = 2 pts | 3 cars = 4 pts",
                    "4 cars = 7 pts | 5 cars = 10 pts | 6 cars = 15 pts",
                    "Completed tickets = + points",
                    "Incomplete tickets = - points",
                    "Longest continuous route = 10 bonus pts"
                ]
            },
            "display_order": 1,
        },
    ],
    "wingspan": [
        {
            "type": "turn_order",
            "content": {
                "title": "Turn Actions (pick one)",
                "items": [
                    "1. Play a Bird (pay food + egg cost)",
                    "2. Gain Food (Forest row - take dice from birdfeeder)",
                    "3. Lay Eggs (Grassland row)",
                    "4. Draw Bird Cards (Wetland row)"
                ]
            },
            "display_order": 0,
        },
        {
            "type": "scoring",
            "content": {
                "title": "Final Scoring",
                "items": [
                    "Bird card point values",
                    "Bonus card points",
                    "Round-end goal points",
                    "1 pt per egg on birds",
                    "1 pt per cached food on birds",
                    "1 pt per tucked card"
                ]
            },
            "display_order": 1,
        },
        {
            "type": "icons",
            "content": {
                "title": "Rounds & Action Cubes",
                "items": [
                    "Round 1: 8 turns",
                    "Round 2: 7 turns",
                    "Round 3: 6 turns",
                    "Round 4: 5 turns"
                ]
            },
            "display_order": 2,
        },
    ],
    "splendor": [
        {
            "type": "turn_order",
            "content": {
                "title": "Turn Actions (pick one)",
                "items": [
                    "1. Take 3 gem tokens of different colors",
                    "2. Take 2 gem tokens of the same color (if 4+ available)",
                    "3. Reserve 1 development card (take 1 gold wildcard token)",
                    "4. Purchase 1 development card (from table or reserved)"
                ]
            },
            "display_order": 0,
        },
        {
            "type": "icons",
            "content": {
                "title": "Gem Types",
                "items": [
                    "Diamond (white) | Sapphire (blue) | Emerald (green)",
                    "Ruby (red) | Onyx (black)",
                    "Gold (yellow) = wildcard, only from reserving",
                    "Max 10 tokens in hand at end of turn"
                ]
            },
            "display_order": 1,
        },
        {
            "type": "scoring",
            "content": {
                "title": "Victory (Goal: 15 Prestige Points)",
                "items": [
                    "Development cards = 0-5 prestige points each",
                    "Noble tiles = 3 prestige points each (auto-visit)",
                    "Game ends at end of round when a player reaches 15 pts",
                    "Highest prestige wins; fewest cards breaks ties"
                ]
            },
            "display_order": 2,
        },
    ],
}


async def seed():
    async with async_session() as db:
        for game_data in GAMES:
            result = await db.execute(select(Game).where(Game.id == game_data["id"]))
            existing = result.scalar_one_or_none()
            if not existing:
                db.add(Game(**game_data))

        await db.flush()

        tutorials_dir = Path(__file__).parent / "data" / "tutorials"
        for tutorial_file in tutorials_dir.glob("*.json"):
            with open(tutorial_file) as f:
                tutorial_data = json.load(f)

            game_id = tutorial_data["gameId"]
            result = await db.execute(
                select(TutorialScript).where(TutorialScript.game_id == game_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                db.add(TutorialScript(
                    game_id=game_id,
                    version="1.0",
                    steps=tutorial_data["steps"],
                    estimated_duration_minutes=len(tutorial_data["steps"]) * 1,
                    is_curated=True,
                ))

        for game_id, refs in QUICK_REFERENCES.items():
            for ref_data in refs:
                result = await db.execute(
                    select(QuickReference).where(
                        QuickReference.game_id == game_id,
                        QuickReference.type == ReferenceType(ref_data["type"]),
                    )
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    db.add(QuickReference(
                        game_id=game_id,
                        type=ReferenceType(ref_data["type"]),
                        content=ref_data["content"],
                        display_order=ref_data["display_order"],
                    ))

        await db.commit()
        print("Seed data inserted successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
