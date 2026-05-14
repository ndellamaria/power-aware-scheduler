# Power-Aware Scheduler
---

## Day 1 — Data Models + Redis Queue

**Goal:** Define the core data structures and get jobs in and out of Redis.

**Progress:**
- [x] `models.py` — `Job`, `GridSignal`, `JobStatus`, `Tolerance`
- [x] `queue.py` — `enqueue`, `get_job`, `update_job_status`, `_to_mapping`, `_from_mapping`
- [x] `requirements.txt`
- [x] `tests/queue_test.py` — round-trip serialize/deserialize test
- [ ] `queue.py` — `dequeue()` (atomic `ZPOPMIN` + `hgetall`)
- [ ] `queue.py` — `set_grid_signal(signal)` / `get_grid_signal()`
- [ ] `config.py` — fill in env var reads + Redis key constants
- [ ] `docker-compose.yml` with Redis
- [ ] Smoke test script — enqueue 3 jobs with different priorities, dequeue and confirm order
- [ ] Expand `queue_test.py` — priority ordering test, empty dequeue returns `None`

**Known issues to fix before moving on:**
- `make_job()` in test uses `datetime.datetime.now()` (naive) — should be
  `datetime.now(timezone.utc)` to match model's `created_at` default
- `config.py` is empty — queue.py doesn't import it yet, so key names are
  hardcoded in the class. Move `QUEUE_KEY` and `JOB_KEY_PREFIX` to config.

**Key decisions to think through:**
- Why a sorted set for the queue (vs list, vs stream)?
- Why store jobs in a separate hash vs inline in the sorted set?
- How do you handle ties in priority (same score)?

**Done when:** You can enqueue a job from a Python script, inspect it in
`redis-cli`, and dequeue it back with correct priority ordering.

---

## Day 2 — Dispatch Loop + Scheduling Policy

**Goal:** A running async loop that pulls jobs from Redis and decides whether
to dispatch them based on the current grid signal.

**Build:**
- Scheduling policy function — pure, no Redis, no asyncio:
  - `should_dispatch(job, signal) -> (bool, reason_str)`
  - `must_run` always dispatches
  - `deferrable` held when `price >= PRICE_DEFER_THRESHOLD`
  - `interruptible` held when `price >= PRICE_BLOCK_THRESHOLD`
  - All tolerances held when `job.power_required_kwh > signal.available_power_kwh`
- Dispatch loop:
  - Poll queue, read grid signal, apply policy
  - If blocked: re-enqueue job, sleep, retry
  - If allowed: hand off to worker (stub for now — just `asyncio.sleep`)
  - Semaphore for max concurrency
- Config via environment variables: `REDIS_URL`, `MAX_WORKERS`,
  `PRICE_DEFER_THRESHOLD`, `PRICE_BLOCK_THRESHOLD`

**Key decisions to think through:**
- When you re-enqueue a blocked job, how do you preserve its queue position?
- What's the tradeoff between polling interval and dispatch latency?
- Why keep the policy as a pure function separate from the loop?

**Done when:** With Redis running and a simulated signal in place, high-price
signals visibly hold `deferrable` jobs while `must_run` jobs dispatch through.

---

## Day 3 — Grid Signal Feed (Simulation)

**Goal:** A background process that publishes realistic, time-varying grid
signals so the scheduler has something to react to.

**Build:**
- Signal feed script (`scripts/signal_feed.py`):
  - Publishes a `GridSignal` to Redis on a configurable interval (e.g. every 5s)
  - Simulates day/night price curve (cheap overnight, expensive midday peak)
  - Simulates grid events: random short spikes above block threshold
  - Simulates carbon intensity varying inversely with price
  - Simulates `available_power_kwh` dropping during events
- Wire the dispatch loop to re-read the signal each iteration (not cached)

**Key decisions to think through:**
- Should signal updates use pub/sub or a simple key write? What are the tradeoffs?
- How stale is too stale for a grid signal? What's a reasonable TTL?
- How does the scheduler behave if the signal feed dies and the key expires?

**Done when:** Running the feed + scheduler together, you can watch jobs
queue up during a simulated price spike and drain when price drops.

---

## Day 4 — Worker Process + Crash Recovery

**Goal:** Real distributed workers that claim jobs, execute them, heartbeat
while running, and get reclaimed if they crash.

**Build:**
- Worker process (`scheduler/worker.py`), runnable as a separate process:
  - Claims a job atomically using `SET NX EX` (claim key with TTL)
  - Runs `_execute(job)` via `asyncio.to_thread` (blocking sim with `time.sleep`)
  - Sends heartbeats that renew the claim TTL while job is running
  - On success: marks `COMPLETED`
  - On failure: retry logic (re-enqueue up to `max_retries`) or dead letter queue
- Crash recovery in the dispatch loop:
  - Scans for jobs marked `RUNNING` with expired claim keys
  - Re-enqueues them as `QUEUED`
- `docker-compose.yml` with `replicas: 2` for worker

**Key decisions to think through:**
- Why `SET NX EX` and not a Redis lock library? What can still go wrong?
- What happens if a worker completes a job but dies before marking it done?
- How long should the claim TTL be relative to the heartbeat interval?
- At-least-once vs at-most-once: which does this design give you, and why?

**Done when:** You can kill a worker mid-job (`docker kill`), watch the claim
expire, and confirm the job is re-enqueued and picked up by the surviving worker.

---

## Day 5 — FastAPI Layer + Job Lifecycle Endpoints

**Goal:** HTTP API to submit jobs and query status.

**Build:**
- `POST /jobs` — validate request, create Job, enqueue, return `{id, status}`
- `GET /jobs/{id}` — look up from Redis hash, return full job state
- `GET /grid/signal` — return current grid signal
- `GET /health` — liveness check (Redis ping)
- Pydantic request/response models (separate from internal dataclasses)
- FastAPI lifespan: start dispatch loop as background task on startup, cancel on shutdown
- Proper HTTP status codes: 202 Accepted on submit, 404 on missing job

**Key decisions to think through:**
- Why 202 and not 201 for job submission?
- The dispatch loop runs in the same process as the API — what are the
  tradeoffs vs running them separately?
- What would you add to make `GET /jobs/{id}` not require polling
  (webhooks, SSE, WebSocket)?

**Done when:** Full end-to-end via `curl`: submit a job, watch it
transition through `queued → running → completed` by polling the status endpoint.

---

## Day 6 — Tests

**Goal:** Test suite that covers the scheduling policy, queue behavior, and
worker crash recovery without requiring a live Redis instance.

**Build:**
- Unit tests for `should_dispatch` — every tolerance/price/power combination
- Unit tests for queue serialization round-trip
- Integration tests using `fakeredis`:
  - Enqueue + dequeue preserves priority ordering
  - `deferrable` job is held under high price signal, dispatches when price drops
  - `must_run` job dispatches regardless of price
  - Failed job is re-enqueued up to `max_retries`, then goes to dead letter
  - Expired claim key triggers re-enqueue
- `pytest.ini` or `pyproject.toml` with `asyncio_mode = "auto"`

**Key decisions to think through:**
- What's the boundary between unit and integration tests here?
- What behavior is impossible to test without real Redis (if anything)?

**Done when:** `pytest` passes with no live Redis, covering all policy
branches and the happy/failure/retry paths.

---

## Day 7 — Polish + Interview Prep

**Goal:** Make the project presentable and make sure you can talk through every decision.

**Build:**
- `README.md`: architecture diagram (ASCII is fine), design decisions section,
  how to run locally, known limitations
- Structured logging throughout (JSON format, include `job_id`, `tolerance`,
  `price`, `reason` on every dispatch decision)
- Review every "Key decisions to think through" question above — have a crisp
  answer for each
- Stretch (if time): `GET /jobs` with status filter, basic metrics endpoint
  (`/metrics` with queue depth, in-flight count, dead letter count)

**Done when:** You can walk someone through the codebase in 10 minutes and
answer "why did you design it this way?" for every major component.

---

## What to be ready to discuss (Emerald-specific)

These are the questions most likely to come up given what they build:

- **Why Redis sorted set and not Kafka/SQS?** (tradeoffs: ordering, persistence, consumer groups)
- **How would you add preemption?** (signal channel into worker, checkpoint/resume, re-queue with preserved state)
- **How would you scale to multiple scheduler nodes?** (leader election vs. distributed claim, partitioning the queue)
- **What does "at-least-once" mean here and what's the failure mode?** (duplicate execution, idempotency requirements)
- **How would you integrate a real LMP feed?** (CAISO/ERCOT APIs, signal freshness, fallback behavior)
- **How would this sit above Kubernetes or Slurm?** (the Conductor model — what's the interface boundary?)
