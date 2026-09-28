import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, NoReturn, TypeAlias

from ..microclient import MicroClient

SubmissionId: TypeAlias = int
Worker: TypeAlias = asyncio.Task[None]
WorkerQueue: TypeAlias = asyncio.Queue[tuple[SubmissionId, Worker]]

logger = logging.getLogger(__name__)


class DownstreamPoller:
    """
    Polls for completed and failed submissions pending downstream egestion, processes
    them concurrently, and marks them as retrieved.
    """

    def __init__(
        self,
        host: str,
        token: str,
        workflow_id: int,
        downstream: Callable[[Any], Awaitable[None]],
        *,
        worker_count: int = 8,
        spawn_rate: float = 1,
        poll_delay: float = 30,
    ):
        self._host = host
        self._token = token
        self._workflow_id = workflow_id
        self._downstream = downstream
        self._worker_count = worker_count
        self._spawn_rate = spawn_rate
        self._poll_delay = poll_delay

        self._worker_slots = asyncio.Semaphore(worker_count)
        self._worker_queue: WorkerQueue = asyncio.Queue(1)
        self._processing_submission_ids: set[SubmissionId] = set()

    async def poll_forever(self) -> NoReturn:  # type: ignore[misc]
        logger.info(
            "Starting downstream poller for: "
            f"host={self._host} "
            f"workflow_id={self._workflow_id} "
            f"worker_count={self._worker_count}"
        )

        async with MicroClient(
            host=self._host,
            is_insights_host=False,
            token=self._token,
            is_bearer_token=False,
        ) as self._client:
            await asyncio.gather(
                self._spawn_workers(),
                *(self._reap_workers() for _ in range(self._worker_count)),
            )

        assert False, "NoReturn"

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
                response = await self._client.graphql(
                    """
                    query GetSubmissionIdsPendingDownstream($workflow_ids: [Int]) {
                        submissions(
                            desc: false
                            filters: {
                                AND: [
                                    {
                                        OR: [
                                            { status: COMPLETE }
                                            { status: FAILED }
                                        ]
                                    }
                                    { filesDeleted: false }
                                    { retrieved: false }
                                ]
                            }
                            limit: 1000
                            orderBy: ID
                            workflowIds: $workflow_ids
                        ) {
                            submissions {
                                id
                            }
                        }
                    }
                    """,
                    {
                        "workflow_ids": [self._workflow_id],
                    },
                )
                submissions = response.submissions.submissions
                submission_ids = set(submission.id for submission in submissions)
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

    async def _worker(self, submission_id: SubmissionId) -> None:
        """
        Process a single submission by retrieving submission metadata and calling
        `self._downstream`. Once completed, mark the submission retrieved.
        """
        logger.info(f"Retrieving metadata for {submission_id=}")
        submission = await self._client.graphql(
            """
            query GetSubmission($submission_id: Int!){
                submission(id: $submission_id){
                    submission_id: id
                    dataset_id: datasetId
                    workflow_id: workflowId
                    status
                    created_at: createdAt
                    updated_at: updatedAt
                    created_by: createdBy
                    updated_by: updatedBy
                    completed_at: completedAt
                    errors
                    files_deleted: filesDeleted
                    input_files: inputFiles {
                        id
                        filename
                        file_path: filepath
                        file_type: filetype
                        file_size: fileSize
                        num_pages: numPages
                    }
                    input_file: inputFile
                    input_filename: inputFilename
                    result_file: resultFile
                    output_files: outputFiles {
                        id
                        file_path: filepath
                        component_id: componentId
                        created_at: createdAt
                    }
                    retrieved: retrieved
                    retries {
                        id
                        previous_errors: previousErrors
                        previous_status: previousStatus
                        retry_errors: retryErrors
                    }
                    reviews {
                        id
                        created_at: createdAt
                        created_by: createdBy
                        started_at: startedAt
                        completed_at: completedAt
                        rejected: rejected
                        review_type: reviewType
                        notes
                    }
                    review_in_progress: reviewInProgress
                }
            }
            """,
            {
                "submission_id": submission_id,
            },
        )

        logger.info(f"Sending {submission_id=} downstream")
        await self._downstream(submission)

        logger.info(f"Marking {submission_id=} retrieved")
        await self._client.graphql(
            """
            mutation UpdateSubmission($submission_id: Int!, $retrieved: Boolean) {
                updateSubmission(submissionId: $submission_id, retrieved: $retrieved) {
                    submission_id: id
                    retrieved
                }
            }
            """,
            {
                "submission_id": submission_id,
                "retrieved": True,
            },
        )

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
