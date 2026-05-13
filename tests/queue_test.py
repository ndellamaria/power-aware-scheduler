import datetime
import uuid 

import pytest 
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

# TODO: write more extensive tests for serialize and deserialize
def test_serialize_deserialize():
    job = make_job()
    serialized = JobQueue._to_mapping(job)
    deserialized = JobQueue._from_mapping(serialized)
    assert deserialized == job