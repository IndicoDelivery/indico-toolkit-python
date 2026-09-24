from typing import TYPE_CHECKING

from indico.queries import GraphQLRequest

if TYPE_CHECKING:
    from typing import Any


class SubmissionIdsPendingAutoReview(GraphQLRequest):  # type: ignore[misc, no-any-unimported]
    QUERY = """
    query SubmissionIdsPendingAutoReview($workflowIds: [Int]) {
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
            workflowIds: $workflowIds
        ) {
            submissions {
                id
            }
        }
    }
    """

    def __init__(self, workflow_id: int):
        super().__init__(self.QUERY, {"workflowIds": [workflow_id]})

    def process_response(self, response: "Any") -> set[int]:
        response = super().process_response(response)
        return {
            submission["id"] for submission in response["submissions"]["submissions"]
        }


class SubmissionIdsPendingDownstream(GraphQLRequest):  # type: ignore[misc, no-any-unimported]
    QUERY = """
    query SubmissionIdsPendingDownstream($workflowIds: [Int]) {
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
            workflowIds: $workflowIds
        ) {
            submissions {
                id
            }
        }
    }
    """

    def __init__(self, workflow_id: int):
        super().__init__(self.QUERY, {"workflowIds": [workflow_id]})

    def process_response(self, response: "Any") -> set[int]:
        response = super().process_response(response)
        return {
            submission["id"] for submission in response["submissions"]["submissions"]
        }
