import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./boardgame.db"

    pydantic_ai_model: str = "openai:gpt-5-nano"
    vision_model: str = "openai:gpt-5-nano"

    openai_api_key: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]
    max_upload_size_mb: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Export API key to environment so the OpenAI SDK can find it
if settings.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
