from indico_toolkit.results import Result, Review


def test_rejected() -> None:
    result = Result(
        submission_id=None,  # type: ignore[ty:invalid-argument-type]
        documents=None,  # type: ignore[ty:invalid-argument-type]
        tasks=None,  # type: ignore[ty:invalid-argument-type]
        predictions=None,  # type: ignore[ty:invalid-argument-type]
        reviews=[
            Review(
                id=None,  # type: ignore[ty:invalid-argument-type]
                reviewer_id=None,  # type: ignore[ty:invalid-argument-type]
                notes=None,  # type: ignore[ty:invalid-argument-type]
                rejected=True,
                type=None,  # type: ignore[ty:invalid-argument-type]
            ),
        ],
    )

    assert result.rejected


def test_unrejected() -> None:
    result = Result(
        submission_id=None,  # type: ignore[ty:invalid-argument-type]
        documents=None,  # type: ignore[ty:invalid-argument-type]
        tasks=None,  # type: ignore[ty:invalid-argument-type]
        predictions=None,  # type: ignore[ty:invalid-argument-type]
        reviews=[
            Review(
                id=None,  # type: ignore[ty:invalid-argument-type]
                reviewer_id=None,  # type: ignore[ty:invalid-argument-type]
                notes=None,  # type: ignore[ty:invalid-argument-type]
                rejected=False,
                type=None,  # type: ignore[ty:invalid-argument-type]
            ),
            Review(
                id=None,  # type: ignore[ty:invalid-argument-type]
                reviewer_id=None,  # type: ignore[ty:invalid-argument-type]
                notes=None,  # type: ignore[ty:invalid-argument-type]
                rejected=True,
                type=None,  # type: ignore[ty:invalid-argument-type]
            ),
            Review(
                id=None,  # type: ignore[ty:invalid-argument-type]
                reviewer_id=None,  # type: ignore[ty:invalid-argument-type]
                notes=None,  # type: ignore[ty:invalid-argument-type]
                rejected=False,
                type=None,  # type: ignore[ty:invalid-argument-type]
            ),
        ],
    )

    assert not result.rejected
