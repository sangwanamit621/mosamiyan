from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Mosamiyan Weather Platform"
    APP_ENV: str = "development"
    PORT: int = 8000
    DEBUG: bool = True

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "mosamiyan"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/mosamiyan"

    # Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # Default Location (New Delhi, India)
    DEFAULT_LAT: float = 28.6139
    DEFAULT_LON: float = 77.2090
    DEFAULT_CITY: str = "New Delhi"
    DEFAULT_COUNTRY: str = "IN"

    # Provider API Keys
    OPENWEATHERMAP_API_KEY: Optional[str] = None
    WEATHERAPI_KEY: Optional[str] = None

    # Cache TTLs (seconds)
    CACHE_TTL_CURRENT: int = 300       # 5 minutes
    CACHE_TTL_HOURLY: int = 1800      # 30 minutes
    CACHE_TTL_DAILY: int = 3600       # 1 hour
    CACHE_TTL_GEO: int = 86400        # 24 hours

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
