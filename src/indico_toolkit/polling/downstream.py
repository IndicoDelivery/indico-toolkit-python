import asyncio
import logging
from typing import TYPE_CHECKING

from indico import AsyncIndicoClient, IndicoConfig
from indico.queries import (
    GetSubmission,
    UpdateSubmission,
)
from indico.types import Submission

from .queries import SubmissionIdsPendingDownstream
from .retry import retry

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import NoReturn, TypeAlias

    SubmissionId: TypeAlias = int
    Worker: TypeAlias = asyncio.Task[None]
    WorkerQueue: TypeAlias = asyncio.Queue[tuple[SubmissionId, Worker]]

logger = logging.getLogger(__name__)


class DownstreamPoller:
    """
    Polls for completed and failed submissions pending downstream egestion, processes
    them concurrently, and marks them as retrieved.
    """

    def __init__(  # type: ignore[no-any-unimported]
        self,
        config: IndicoConfig,
        workflow_id: int,
        downstream: "Callable[[Submission], Awaitable[None]]",
        *,
        worker_count: int = 8,
        spawn_rate: float = 1,
        poll_delay: float = 30,
        retry_count: int = 4,
        retry_wait: float = 1,
        retry_backoff: float = 4,
        retry_jitter: float = 0.5,
    ):
        self._config = config
        self._workflow_id = workflow_id
        self._downstream = downstream
        self._worker_count = worker_count
        self._spawn_rate = spawn_rate
        self._poll_delay = poll_delay

        self._retry = retry(
            Exception,
            count=retry_count,
            wait=retry_wait,
            backoff=retry_backoff,
            jitter=retry_jitter,
        )
        self._worker_slots = asyncio.Semaphore(worker_count)
        self._worker_queue: "WorkerQueue" = asyncio.Queue(1)
        self._processing_submission_ids: "set[SubmissionId]" = set()

    async def poll_forever(self) -> "NoReturn":  # type: ignore[misc]
        logger.info(
            "Starting downstream poller for: "
            f"host={self._config.host} "
            f"workflow_id={self._workflow_id} "
            f"worker_count={self._worker_count}"
        )

        async with AsyncIndicoClient(self._config) as client:
            self._client_call = self._retry(client.call)
            await asyncio.gather(
                self._spawn_workers(),
                *(self._reap_workers() for _ in range(self._worker_count)),
            )

    async def _spawn_workers(self) -> None:
        """
        Poll for completed and failed submissions and spawn workers to send them
        downstream. `self._worker_slots` limits the number of workers that can run
        concurrently. Submission IDs in progress are tracked with
        `self._processing_submission_ids`.
        """
        logger.info(
            f"Polling submissions pending downstream every {self._poll_delay} seconds"
        )

        while True:
            try:
                submission_ids: "set[SubmissionId]" = await self._client_call(
                    SubmissionIdsPendingDownstream(self._workflow_id)
                )
            except Exception:
                logger.exception("Error occurred while polling submissions")
                await asyncio.sleep(self._poll_delay)
                continue

            submission_ids -= self._processing_submission_ids

            if not submission_ids:
                await asyncio.sleep(self._poll_delay)
                continue

            for submission_id in submission_ids:
                await self._worker_slots.acquire()
                logger.info(f"Spawning worker for {submission_id=}")
                self._processing_submission_ids.add(submission_id)
                worker = asyncio.create_task(self._worker(submission_id))
                await self._worker_queue.put((submission_id, worker))
                await asyncio.sleep(1 / self._spawn_rate)

    async def _worker(self, submission_id: "SubmissionId") -> None:
        """
        Process a single submission by retrieving submission metadata and calling
        `self._downstream`. Once completed, mark the submission retrieved.
        """
        logger.info(f"Retrieving metadata for {submission_id=}")
        submission = await self._client_call(GetSubmission(submission_id))

        logger.info(f"Sending {submission_id=} downstream")
        await self._downstream(submission)

        logger.info(f"Marking {submission_id=} retrieved")
        await self._client_call(UpdateSubmission(submission_id, retrieved=True))

        logger.info(f"Completed dowstream of {submission_id=}")

    async def _reap_workers(self) -> None:
        """
        Reap completed workers, releasing their slots for new tasks. Log errors for
        submissions that failed to process. Remove their submission IDs from
        `self._processing_submission_ids` to be retried.
        """
        while True:
            submission_id, worker = await self._worker_queue.get()

            try:
                await worker
            except Exception:
                logger.exception(f"Error occurred while processing {submission_id=}")

            self._processing_submission_ids.remove(submission_id)
            self._worker_slots.release()
