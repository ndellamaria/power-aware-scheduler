from scheduler.models import Job, JobStatus, Tolerance
from uuid import UUID
import datetime
import itertools

from redis.asyncio import Redis

class JobQueue:

    QUEUE_KEY = "job:queue"
    JOB_KEY_PREFIX = "job:"

    def __init__(self, redis: Redis):
        self.redis = redis
        # seq to handle priority ties
        # TODO: is this safe if we have multiple workers?
        self.seq = itertools.count(start=0)

    @staticmethod
    def _to_mapping(job: Job) -> dict[str, str]:
        return {
            "id": str(job.id),
            "payload": job.payload,
            "priority": str(job.priority),
            "power_required_kwh": str(job.power_required_kwh),
            "tolerance": job.tolerance.value,
            "deadline": job.deadline.isoformat() if job.deadline else "",
            "max_retries": str(job.max_retries),
            "duration_seconds": str(job.duration_seconds),
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
        }

    @staticmethod
    def _from_mapping(data: dict) -> Job:
        return Job(
            id=UUID(data["id"]),
            payload=data["payload"],
            priority=int(data["priority"]),
            power_required_kwh=float(data["power_required_kwh"]),
            tolerance=Tolerance(data["tolerance"]),
            deadline=datetime.datetime.fromisoformat(data["deadline"]) if data["deadline"] else None,
            max_retries=int(data["max_retries"]),
            duration_seconds=float(data["duration_seconds"]),
            status=JobStatus(data["status"]),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
        )

    async def enqueue(self, job: Job) -> None:
        print(f"Enqueuing job {job.id}")
        job_key = f"{self.JOB_KEY_PREFIX}{job.id}"
        score = -job.priority + (next(self.seq) / 10_000_000)
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zadd(self.QUEUE_KEY, {job_key: score}, nx=True)
            pipe.hset(job_key, mapping=self._to_mapping(job))
            await pipe.execute()

    async def update_job_status(self, job_id: UUID, status: JobStatus) -> None:
        job_key = f"{self.JOB_KEY_PREFIX}{job_id}"
        await self.redis.hset(job_key, "status", status.value)

    async def get_job(self, job_id: UUID) -> Job | None:
        job_key = f"{self.JOB_KEY_PREFIX}{job_id}"
        data = await self.redis.hgetall(job_key)
        if not data:
            return None
        return self._from_mapping(data)
