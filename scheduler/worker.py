import time
import threading
from models import WorkerState, Job, JobStatus
from job_queue import JobQueue
from typing import List 

MAX_WORKERS = 10

# Single thread worker that pulls from jobqueue and executes
class Worker(threading.Thread): 
    id: str
    state: WorkerState


    def __init__(self, id: str, job_queue: JobQueue, result_queue: List, state: WorkerState = WorkerState.IDLE):
        super().__init__()
        self.id = id
        self.state = state
        self.job_queue = job_queue
        self.result_queue = result_queue
        self._stop = threading.Event()


    # run as loop that pulls from job queue and executes
    def run(self) -> Job | None:
        while not self._stop.is_set():
            job = self.job_queue.pop()
            if job: 
                job.status = JobStatus.RUNNING
                self.state = WorkerState.BUSY
                time.sleep(job.duration)
                job.status = JobStatus.COMPLETED
                self.state = WorkerState.IDLE
                self.result_queue.append([job.id, job.status])
            else:
                # pause for 1 second to avoid 100% cpu usage and check for stop condition 
                time.sleep(1)
                continue

    def stop(self): 
        # set the stop event to true
        self._stop.set()


class WorkerPool: 

    def __init__(self, job_queue: JobQueue, result_queue: List, max_workers: int = MAX_WORKERS): 
        self.workers = [Worker(f"worker-{i}", job_queue, result_queue) for i in range(max_workers)]

    def start(self): 
        for worker in self.workers: 
            worker.start()

    def get_status(self) -> list[WorkerState]:
        return [worker.state for worker in self.workers]

    def stop(self): 
        for worker in self.workers: 
            worker.stop()

        for worker in self.workers: 
            worker.join()