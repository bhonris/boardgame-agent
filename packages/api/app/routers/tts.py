import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.schemas.game import TTSRequest

router = APIRouter(prefix="/api", tags=["tts"])


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="TTS service not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": "tts-1",
                    "input": request.text,
                    "voice": request.voice,
                    "response_format": "mp3",
                },
                timeout=30.0,
            )
            response.raise_for_status()

        return StreamingResponse(
            iter([response.content]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline"},
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"TTS provider error: {e.response.status_code}")
