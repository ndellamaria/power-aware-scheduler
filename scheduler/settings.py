from pydantic_settings import BaseSettings
from pydantic_core import Field
from functools import lru_cache

class Settings(BaseSettings):
    redis_url: str = Field(..., env="REDIS_URL")
    queue_key: str = Field(..., env="QUEUE_KEY")
    job_key_prefix: str = Field(..., env="JOB_KEY_PREFIX")
    grid_signal_key: str = Field(..., env="GRID_SIGNAL_KEY")
    grid_signal_ttl_seconds: int = Field(..., env="GRID_SIGNAL_TTL_SECONDS")
    grid_price_threshold: float = Field(..., env="GRID_PRICE_THRESHOLD")
    worker_poll_interval: float = Field(..., env="WORKER_POLL_INTERVAL")
    claim_ttl_seconds: int = Field(..., env="CLAIM_TTL_SECONDS")
    log_level: str = Field(..., env="LOG_LEVEL")

@lru_cache
def get_settings() -> Settings:
    return Settings()