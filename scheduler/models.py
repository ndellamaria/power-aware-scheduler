import uuid
import datetime
from enum import Enum
from dataclasses import dataclass, field

class Tolerance(Enum):
    MUST_RUN = "must_run"
    DEFERRABLE = "deferrable"
    INTERRUPTIBLE = "interruptible"


class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    DEAD_LETTERED = "dead_letter_queued"


@dataclass(frozen=True)
class Job:
    payload: str
    priority: int
    power_required_kwh: float
    tolerance: Tolerance
    deadline: datetime.datetime | None
    max_retries: int
    duration_seconds: float
    status: JobStatus
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

@dataclass
class GridSignal: 
    price_per_kwh: float
    carbon_intensity: float
    available_power_kwh: float
    timestamp: datetime.datetime