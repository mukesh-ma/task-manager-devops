"""
Centralized application configuration using Pydantic Settings.
All values are overridable via environment variables, which is what lets
the exact same Docker image run unmodified across dev, staging and prod.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Task Manager API"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql://taskuser:taskpass@localhost:5432/taskdb"

    # Redis (used for response caching + rate limiting)
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Observability
    enable_metrics: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
