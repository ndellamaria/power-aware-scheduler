import datetime
import uuid 

import pytest 
from fakeredis.aioredis import FakeRedis
from scheduler.models import Job, JobStatus, Tolerance
from scheduler.queue import JobQueue

def make_job(**kwargs) -> Job:
    defaults = {
        "id": uuid.uuid4(),
        "payload": "test payload",
        "priority": 1,
        "power_required_kwh": 1.0,
        "tolerance": Tolerance.MUST_RUN,
        "deadline": datetime.datetime.now() + datetime.timedelta(hours=1),
        "max_retries": 0,
        "duration_seconds": 10,
        "status": JobStatus.QUEUED,
        "created_at": datetime.datetime.now(),
    }
    defaults.update(kwargs)
    return Job(**defaults)

def test_enqueue_score_fraction_stays_in_unit_interval():
    """Tie-break must never reach 1.0 or priority ordering inverts after many enqueues."""
    for seq in (0, 1, 10_000_000, 10**12):
        frac = JobQueue._enqueue_score(0, seq) - (-0)
        assert 0.0 <= frac < 1.0


def test_enqueue_score_no_priority_inversion_after_many_enqueues():
    """Regression: seq/10_000_000 would reach 1.0 and let a lower priority outrank a higher one."""
    high_p_low_seq = JobQueue._enqueue_score(100, 0)
    low_p_very_old_seq = JobQueue._enqueue_score(99, 10_000_000)
    assert high_p_low_seq < low_p_very_old_seq


def test_enqueue_score_fifo_within_same_priority():
    first = JobQueue._enqueue_score(5, 0)
    second = JobQueue._enqueue_score(5, 1)
    assert first < second


# TODO: write more extensive tests for serialize and deserialize
def test_serialize_deserialize():
    job = make_job()
    serialized = JobQueue._to_mapping(job)
    deserialized = JobQueue._from_mapping(serialized)
    assert deserialized == job

@pytest.fixture
async def queue_fixture() -> JobQueue: 
    redis = FakeRedis(decode_responses=True)
    return JobQueue(redis)

@pytest.mark.asyncio
async def test_enqueue_dequeue(queue_fixture: JobQueue):
    job = make_job()
    await queue_fixture.enqueue(job)
    assert await queue_fixture.dequeue(queue_fixture.redis) == job
