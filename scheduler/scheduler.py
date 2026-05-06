from job_queue import JobQueue
from worker import WorkerPool
from models import Job, JobStatus    
import uuid
from typing import List, Tuple
import time
import threading
import queue

class Scheduler(): 

    def __init__(self): 
        self.result_store: dict[uuid.UUID, JobStatus] = {}
        self.result_queue: queue.Queue = queue.Queue()
        self.job_queue = JobQueue()
        self.worker_pool = WorkerPool(self.job_queue, self.result_queue)
        self._stop = threading.Event()
        self.job_retries: dict[uuid.UUID, int] = {}
        self.dead_letter_queue: List[Job] = []
        super().__init__()

    
    def start(self): 
        self.worker_pool.start()
        self._collect_thread = threading.Thread(target=self._collect)
        self._collect_thread.start()

    def stop(self): 
        self.worker_pool.stop()
        self._stop.set()
        self._collect_thread.join()

    def schedule(self, job: Job): 
        self.job_queue.push(job)
        self.job_retries[job.id] = job.max_retries
        return True

    def _collect(self): 
        # background thread that collects results from the worker pool
        while not self._stop.is_set():
            results = self.result_queue.get(block=True, timeout=1)
            if results:
                job, status = results
                if status == JobStatus.FAILED:
                    if self.at_max_retries(job.id):
                        self.dead_letter_queue.append(job)
                    else:
                        self.job_retries[job.id] -= 1
                        self.job_queue.push(job)
                else:
                    self.result_store[job.id] = status
            else:
                time.sleep(1)
                continue


    def at_max_retries(self, job_id: uuid.UUID) -> bool: 
        if self.job_retries[job_id] <= 0:
            return True
        return False
