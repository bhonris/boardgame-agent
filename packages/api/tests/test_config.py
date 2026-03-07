import pytest

from app.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            database_url_sync="postgresql://test:test@localhost/test",
        )
        assert s.pydantic_ai_model == "openai:gpt-4o"
        assert s.max_upload_size_mb == 10
        assert "http://localhost:5173" in s.cors_origins

    def test_custom_model(self):
        s = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            database_url_sync="postgresql://test:test@localhost/test",
            pydantic_ai_model="anthropic:claude-sonnet-4-6",
        )
        assert s.pydantic_ai_model == "anthropic:claude-sonnet-4-6"
