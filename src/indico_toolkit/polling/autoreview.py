import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, NoReturn, TypeAlias

from .. import etloutput, results
from ..etloutput import EtlOutput
from ..microclient import MicroClient
from ..results import Document, Result

SubmissionId: TypeAlias = int
Worker: TypeAlias = asyncio.Task[None]
WorkerQueue: TypeAlias = asyncio.Queue[tuple[SubmissionId, Worker]]

logger = logging.getLogger(__name__)


@dataclass
class AutoReviewed:
    changes: list[dict[str, Any]]
    reject: bool = False
    stp: bool = False


class AutoReviewPoller:
    """
    Polls for submissions requiring auto review, processes them,
    and submits the review results concurrently.
    """

    def __init__(
        self,
        host: str,
        token: str,
        workflow_id: int,
        auto_review: Callable[
            [Result, dict[Document, EtlOutput]],
            Awaitable[AutoReviewed],
        ],
        *,
        worker_count: int = 8,
        spawn_rate: float = 1,
        poll_delay: float = 30,
        load_etl_output: bool = True,
        load_text: bool = True,
        load_tokens: bool = True,
        load_tables: bool = True,
    ):
        self._host = host
        self._token = token
        self._workflow_id = workflow_id
        self._auto_review = auto_review
        self._worker_count = worker_count
        self._spawn_rate = spawn_rate
        self._poll_delay = poll_delay
        self._load_etl_output = load_etl_output
        self._load_text = load_text
        self._load_tokens = load_tokens
        self._load_tables = load_tables

        self._worker_slots = asyncio.Semaphore(worker_count)
        self._worker_queue: WorkerQueue = asyncio.Queue(1)
        self._processing_submission_ids: set[SubmissionId] = set()

    async def poll_forever(self) -> NoReturn:  # type: ignore[misc]
        logger.info(
            "Starting auto review poller for: "
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
        Poll for submissions pending auto review and spawn workers to process them.
        `self._worker_slots` limits the number of workers that can run concurrently.
        Submission IDs in progress are tracked with `self._processing_submission_ids`.
        """
        logger.info(
            f"Polling submissions pending auto review every {self._poll_delay} seconds"
        )

        while True:
            try:
                response = await self._client.graphql(
                    """
                    query GetSubmissionIdsPendingAutoReview($workflow_ids: [Int]) {
                        submissions(
                            desc: false
                            filters: {
                                AND: [
                                    { status: PENDING_AUTO_REVIEW }
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
        Process a single submission by retrieving submission metadata, the result file,
        etl output, calling `self._auto_review`, and submitting changes.
        """
        logger.info(f"Retrieving metadata for {submission_id=}")
        response = await self._client.graphql(
            """
            query GetSubmission($submission_id: Int!) {
                submission(id: $submission_id) {
                    result_file: resultFile
                    status
                }
            }
            """,
            {
                "submission_id": submission_id,
            },
        )
        submission = response.submission

        logger.info(f"Retrieving results for {submission_id=}")
        result = await results.load_async(
            submission.result_file,
            reader=self._client.storage,
        )

        if self._load_etl_output:
            logger.info(f"Retrieving etl output for {submission_id=}")
            etl_outputs = {
                document: await etloutput.load_async(
                    document.etl_output_uri,
                    reader=self._client.storage,
                    text=self._load_text,
                    tokens=self._load_tokens,
                    tables=self._load_tables,
                )
                for document in result.documents
                if not document.failed
            }
        else:
            logger.info(f"Skipping etl output for {submission_id=}")
            etl_outputs = {}

        logger.info(f"Applying auto review for {submission_id=}")
        auto_reviewed = await self._auto_review(result, etl_outputs)

        logger.info(f"Submitting auto review for {submission_id=}")
        response = await self._client.graphql(
            """
            mutation SubmitAutoReview(
                $submission_id: Int!
                $changes: JSONString!
                $straight_through_process: Boolean!
                $reject: Boolean!
            ) {
                submitAutoReview(
                    submissionId: $submission_id
                    changes: $changes
                    forceComplete: $straight_through_process
                    rejected: $reject
                ) {
                    id: jobId
                }
            }
            """,
            {
                "submission_id": submission_id,
                "changes": (
                    json.dumps(auto_reviewed.changes)
                    if auto_reviewed.changes is not None
                    else None
                ),
                "straight_through_process": auto_reviewed.stp,
                "reject": auto_reviewed.reject,
            },
        )
        job = response.submitAutoReview
        job.status = "PENDING"

        while job.status in ("PENDING", "RECEIVED", "STARTED"):
            response = await self._client.graphql(
                """
                query GetJob($job_id: String!) {
                    job(id: $job_id) {
                        id
                        status
                        result
                    }
                }
                """,
                {
                    "job_id": job.id,
                },
            )
            job = response.job

        if job.status == "SUCCESS":
            logger.info(f"Completed auto review of {submission_id=}")
        else:
            logger.error(
                f"Submit failed for {submission_id=}: {job.status=!r} {job.result=!r}"
            )

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
