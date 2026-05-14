from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCHEDULER_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    redis_url: str = "redis://localhost:6379/0"
    queue_key: str = "job:queue"
    job_key_prefix: str = "job:"
    grid_signal_key: str = "grid:signal"
    grid_signal_ttl_seconds: int = 60
    grid_price_threshold: float = 0.10
    worker_poll_interval: float = 1.0
    claim_ttl_seconds: int = 30
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
