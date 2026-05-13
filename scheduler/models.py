import uuid
import datetime
from enum import Enum
from dataclasses import dataclass, field

@dataclass
class Tolerance(Enum):
    MUST_RUN = "must_run"
    DEFERABLE = "deferrable"
    INTERRUPTIBLE = "interruptible"

@dataclass
class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    DEAD_LETTERED = "dead_letter_queued"

@dataclass(frozen=True)
class Job: 
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    payload: str
    priority: int
    power_required_kwh: float
    tolerance: Tolerance
    deadline: datetime.datetime | None
    max_retries: int
    duration_seconds: float
    status: JobStatus
    created_at: datetime.datetime = datetime.datetime.now()

@dataclass
class GridSignal: 
    price_per_kwh: float
    carbon_intensity: float
    available_power_kwh: float
    timestamp: datetime.datetime