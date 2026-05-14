import uuid
import datetime
from enum import Enum
from dataclasses import dataclass, field    
import json

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

    # TODO: move encoding/decoding to queue.py?

@dataclass
class GridSignal: 
    price_per_kwh: float
    carbon_intensity: float
    available_power_kwh: float
    timestamp: datetime.datetime

    # TODO: add error handling? 
    def to_json(self) -> str:
        return json.dumps({"price_per_kwh": self.price_per_kwh, "carbon_intensity": self.carbon_intensity, "available_power_kwh": self.available_power_kwh, "timestamp": self.timestamp.isoformat()})

    # TODO: add error handling? 
    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        return GridSignal(price_per_kwh=data["price_per_kwh"], carbon_intensity=data["carbon_intensity"], available_power_kwh=data["available_power_kwh"], timestamp=datetime.datetime.fromisoformat(data["timestamp"]))