import pytest

from app.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings(
            database_url="sqlite+aiosqlite:///./test.db",
        )
        assert s.pydantic_ai_model in ("openai:gpt-5-nano", "openai:gpt-4o")
        assert s.max_upload_size_mb == 10
        assert "http://localhost:5173" in s.cors_origins

    def test_custom_model(self):
        s = Settings(
            database_url="sqlite+aiosqlite:///./test.db",
            pydantic_ai_model="anthropic:claude-sonnet-4-6",
        )
        assert s.pydantic_ai_model == "anthropic:claude-sonnet-4-6"
