"""
A feature-complete auto review polling script that incorporates asyncio,
automatic retry, result file dataclasses, and etl output dataclasses.

Max workers, spawn rate, and etl output loading are all configurable.
See the `AutoReviewPoller` class definition.
"""

import asyncio
import sys
from operator import attrgetter
from pathlib import Path

from indico_toolkit.etloutput import EtlOutput
from indico_toolkit.polling import AutoReviewed, AutoReviewPoller
from indico_toolkit.results import Document, Extraction, Result


async def auto_review(
    result: Result,
    etl_outputs: dict[Document, EtlOutput],
) -> AutoReviewed:
    """
    Apply auto review rules to predictions and determine straight through processing.
    Any IO performed (network requests, file reads/writes, etc) must be awaited to
    avoid blocking the asyncio loop that schedules this coroutine.
    """
    predictions = result.pre_review
    extractions = predictions.extractions

    # Downselect all labels from all tasks based on highest confidence.
    for task, extractions in extractions.groupby(attrgetter("task")).items():
        for label, extractions in extractions.groupby(attrgetter("label")).items():
            # Order extractions by confidence descending.
            ordered = extractions.orderby(attrgetter("confidence"), reverse=True)
            ordered.reject()  # Reject all extractions.
            ordered[0].unreject()  # Unreject the highest confidence extraction.

    confidence_thresholds = {
        "From": 0.99,
        "To": 0.97,
        "Subject": 0.90,
        "Date": 0.99999,
    }

    # Auto accept predictions based on label's confidence threshold.
    for label, threshold in confidence_thresholds.items():
        extractions.where(label=label, min_confidence=threshold).accept()

    # Reject all predictions with confidence below 75%.
    extractions.where(max_confidence=0.75).reject()

    # Apply name normalization to all predictions with the "Name" label.
    extractions.where(label="Name").apply(normalize_name)

    return AutoReviewed(
        changes=predictions.to_changes(result),
        reject=False,  # Defaults to `False` and may be omitted.
        stp=False,  # Defaults to `False` and may be omitted.
    )


def normalize_name(extraction: Extraction) -> None:
    """
    Normalize 'Last, First' to 'First Last'.
    """
    names = extraction.text.split(",")

    if len(names) == 2:
        last, first = names
        extraction.text = first.strip() + " " + last.strip()



if __name__ == "__main__":
    import logging

    logging.basicConfig(
        format=(
            r"[%(asctime)s] "
            r"%(name)s:%(funcName)s():%(lineno)s: "
            r"%(levelname)s %(message)s"
        ),
        level=logging.INFO,
        force=True,
    )
    workflow_id = int(sys.argv[1])
    asyncio.run(
        AutoReviewPoller(
            "try.indico.io",
            Path("indico_api_token.txt").read_text(),
            workflow_id,
            auto_review,
        ).poll_forever()
    )
