from operator import truediv
from queue import PriorityQueue, Empty
from itertools import count
from models import Job
from dataclasses import dataclass

@dataclass(init=True)
class JobQueue:
    _pq: PriorityQueue = PriorityQueue()
    _seq: count = count()

    def push(self, job: Job): 
        # use sequence as tie breaker for priority 
        self._pq.put((-job.priority, next(self._seq), job))

    def pop(self) -> Job | None:
        # return job at index 2 of the tuple (priority, sequence, job) 
        try: 
            return self._pq.get_nowait()[2]
        except Empty:
            return None

    