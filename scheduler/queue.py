from datetime import datetime
import itertools
from uuid import UUID

from redis.asyncio import Redis

from scheduler.models import GridSignal, Job, JobStatus, Tolerance
from scheduler.settings import get_settings

class JobQueue:


    def __init__(self, redis: Redis):
        self.redis = redis
        # seq to handle priority ties
        # TODO: is this safe if we have multiple workers?
        self.seq = itertools.count(start=0)
        self.settings = get_settings()

    @staticmethod
    def _enqueue_score(priority: int, seq: int) -> float:
        # Lower score is dequeued first. Higher `priority` must always sort
        # before lower `priority`, with FIFO among ties. 
        # seq/(seq+1) stays in [0, 1)
        return -priority + (seq / (seq + 1.0))

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
            deadline=datetime.fromisoformat(data["deadline"]) if data["deadline"] else None,
            max_retries=int(data["max_retries"]),
            duration_seconds=float(data["duration_seconds"]),
            status=JobStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    async def enqueue(self, job: Job) -> None:
        print(f"Enqueuing job {job.id}")
        job_key = f"{self.settings.job_key_prefix}{job.id}"
        score = self._enqueue_score(job.priority, next(self.seq))
        
        # TODO: watch with optimistic locking? nx=True? 
        # redis pipeline with transaction to ensure atomicity when 
        # updating job status 
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zadd(self.settings.queue_key, {job_key: score})
            pipe.hset(job_key, mapping=self._to_mapping(job))
            await pipe.execute()

    # for multi-writer scenario, need WATCH to ensure atomicity (?)
    async def update_job_status(self, job_id: UUID, status: JobStatus) -> None:
        job_key = f"{self.settings.job_key_prefix}{job_id}"
        await self.redis.hset(job_key, "status", status.value)

    async def get_job(self, job_id: UUID) -> Job | None:
        job_key = f"{self.settings.job_key_prefix}{job_id}"
        data = await self.redis.hgetall(job_key)
        if not data:
            return None
        return self._from_mapping(data)

    async def dequeue(self, redis: Redis) -> Job | None:
        job = await redis.zpopmin(self.QUEUE_KEY, count=1)
        if not job:
            return None
        # job is a list of tuples [(job_key, score)]
        # job[0] is the first tuple, [0][0] is the job_key
        job_key = job[0][0]
        job_data = await redis.hgetall(job_key)
        if not job_data:
            return None
        return self._from_mapping(job_data)

    async def set_grid_signal(self, redis: Redis, signal: GridSignal) -> None:
        # TODO: add error handling? 
        grid_signal_serialized = signal.to_json()
        # handle expiry when reading signal from redis so we can log, count, etc.
        await redis.set(self.settings.grid_signal_key, grid_signal_serialized)
        return 

    async def get_grid_signal(self, redis: Redis) -> GridSignal | None:
        grid_signal_serialized = await redis.get(self.GRID_SIGNAL_KEY)
        if not grid_signal_serialized:
            return None
        # TODO: add error handling? 
        return GridSignal.from_json(grid_signal_serialized)