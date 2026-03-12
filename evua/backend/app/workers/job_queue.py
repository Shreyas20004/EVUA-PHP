"""
In-Memory Job Queue
Tracks background migration jobs.
"""
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Coroutine, Optional

logger = logging.getLogger("evua.job_queue")


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    job_id: str
    state: JobState = JobState.PENDING
    result: Any = None
    error: Optional[str] = None
    progress: dict = field(default_factory=dict)


class JobQueue:
    """
    Simple in-memory job registry with asyncio background execution.

    Jobs are stored in a dict keyed by job_id.  A background task is
    launched for each job via :meth:`submit`.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create_job(self) -> str:
        """Register a new job and return its ID."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = Job(job_id=job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def all_jobs(self) -> list[Job]:
        return list(self._jobs.values())

    def submit(
        self,
        job_id: str,
        coro: Coroutine,
    ) -> asyncio.Task:
        """
        Schedule *coro* as a background asyncio task.

        The job's state is updated automatically:
        - RUNNING while the coroutine executes
        - COMPLETED on success (result stored)
        - FAILED on exception (error message stored)
        """
        async def _wrapped():
            job = self._jobs[job_id]
            job.state = JobState.RUNNING
            try:
                job.result = await coro
                job.state = JobState.COMPLETED
                logger.info("Job %s completed", job_id)
            except Exception as exc:
                job.state = JobState.FAILED
                job.error = str(exc)
                logger.error("Job %s failed: %s", job_id, exc, exc_info=True)

        task = asyncio.create_task(_wrapped())
        return task


# Global singleton used across the application
job_queue = JobQueue()
