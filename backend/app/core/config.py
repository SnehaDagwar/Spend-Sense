from functools import lru_cache

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Spend Sense API"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "local"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/spend_sense"
    BACKEND_CORS_ORIGINS: list[str | AnyUrl] = Field(default_factory=list)

    # AI Insights and Financial Intelligence Config
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    CLAUDE_API_KEY: str | None = None
    CLAUDE_MODEL: str = "claude-3-5-haiku-20241022"
    AI_DAILY_RATE_LIMIT: int = 10
    AI_BURST_RATE_LIMIT: int = 5          # max requests per 60-second window
    AI_REQUEST_TIMEOUT: int = 30          # seconds per provider HTTP call
    AI_MAX_RESPONSE_TOKENS: int = 4000    # max_tokens sent to provider
    AI_FALLBACK_ENABLED: bool = True      # use rule-based fallback on provider failure
    AI_CACHE_MAX_SIZE: int = 500          # max cached insight entries (LRU eviction)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
