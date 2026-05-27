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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
