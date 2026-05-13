import json
from scheduler.models import Job, JobStatus, Tolerance
from uuid import UUID
import datetime

def _serialize(job: Job) -> str: 
    # make sure all fields are json serializable 
    data = {
        "id": str(job.id),
        "payload": job.payload,
        "priority": job.priority,
        "power_required_kwh": float(job.power_required_kwh),
        "tolerance": job.tolerance.value,
        "deadline": job.deadline.isoformat() if job.deadline else None,
        "max_retries": int(job.max_retries),
        "duration_seconds": float(job.duration_seconds),
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
    }
    return json.dumps(data)

def _deserialize(data: str) -> Job:
    data = json.loads(data)
    return Job(
        id=UUID(data["id"]),
        payload=data["payload"],
        priority=int(data["priority"]),
        power_required_kwh=float(data["power_required_kwh"]),
        tolerance=Tolerance(data["tolerance"]),
        deadline=datetime.datetime.fromisoformat(data["deadline"]) if data["deadline"] else None,
        max_retries=int(data["max_retries"]),
        duration_seconds=float(data["duration_seconds"]),
        status=JobStatus.from_value(data["status"]),
        created_at=datetime.datetime.fromisoformat(data["created_at"]),
    )

