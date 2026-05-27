from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = Field(default="", repr=False)
    groq_model: str = "openai/gpt-oss-120b"
    groq_max_context_tokens: int = 90_000
    groq_default_max_completion_tokens: int = 2_048
    database_url: str = "sqlite:///data/assistant.db"
    local_timezone: str = "Asia/Kolkata"
    google_credentials_path: str = "data/google/credentials.json"
    google_token_path: str = "data/google/token.json"
    google_calendar_default_id: str = "primary"
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
