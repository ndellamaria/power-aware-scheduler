from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"

    # Grid signal
    grid_signal_ttl_seconds: int = 60
    grid_price_threshold: float = 0.10

    # Worker
    worker_poll_interval: float = 1.0
    claim_ttl_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Redis keys — stable identifiers, not runtime config
QUEUE_KEY = "job:queue"
JOB_KEY_PREFIX = "job:"
GRID_SIGNAL_KEY = "grid:signal"
