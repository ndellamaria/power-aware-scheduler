import uuid 
import datetime 
from enum import Enum
from dataclasses import dataclass


@dataclass(init=True)
class Job: 
    id: uuid.UUID = uuid.uuid4()
    payload: str 
    priority: int = 1
    power_budget_kwh: float = 0.0
    deadline: datetime.datetime | None = None
    max_retries: int # TODO: should this be per job or universal? 
    duration_seconds: float = 0.0

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkerState(Enum): 
    IDLE = "idle"
    BUSY = "busy"
    DEAD = "dead"



