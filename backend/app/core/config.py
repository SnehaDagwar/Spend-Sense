from functools import lru_cache

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Spend Sense API"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "local"

    # ── JWT / Auth ────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "spend-sense-api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/spend_sense"
    BACKEND_CORS_ORIGINS: list[str | AnyUrl] = Field(default_factory=list)

    # ── Rate Limiting ─────────────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10    # login, register, refresh
    RATE_LIMIT_API_PER_MINUTE: int = 120    # all other authenticated endpoints

    # ── Response Cache ────────────────────────────────────────────────────
    CACHE_ANALYTICS_TTL_SECONDS: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000

    # ── OpenAPI ───────────────────────────────────────────────────────────
    OPENAPI_ENABLED: bool = True

    # ── AI Insights and Financial Intelligence Config ─────────────────────
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

    # ── Monitoring ────────────────────────────────────────────────────────────
    # Set SENTRY_DSN to enable Sentry error tracking in production.
    # Leave unset (or empty) to disable Sentry entirely.
    SENTRY_DSN: str | None = None

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def _validate_secret_key(cls, v: str, info: object) -> str:
        # Defer import to avoid circular dependency at module load time
        import os
        env = os.environ.get("ENVIRONMENT", "local")
        if env not in ("test", "local") and len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters in non-local/test environments. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
