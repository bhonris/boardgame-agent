from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/boardgame"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/boardgame"

    pydantic_ai_model: str = "openai:gpt-4o"
    vision_model: str = "openai:gpt-4o"

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]
    max_upload_size_mb: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
