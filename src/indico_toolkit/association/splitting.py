import re
from copy import deepcopy
from itertools import zip_longest
from typing import Any, Dict, Iterator


def split_prediction(
    prediction: Dict[str, Any], separator: str = r"\s*\n\s*"
) -> Iterator[Dict[str, Any]]:
    """
    Split a single `prediction` into mutiple predictions along a `separator` regex
    and yield new predictions having updated text and spans. By default, split on
    newlines (including adjacent whitespace).
    """

    # re.split (with group capture) returns a sequence of text values and delimiters:
    # ["some", "\n", "separated", "\n", "text"]
    # The text values are the even elements:
    # ["some", "separated", "text"]
    # The delimeters are the odd elements:
    # ["\n", "\n"]
    # zip_longest pairs them together without losing the last text value:
    # [("some", "\n"), ("separated", "\n"), ("text", None)]
    texts_and_delimiters = re.split(f"({separator})", prediction["text"])
    texts = texts_and_delimiters[::2]
    delimiters = texts_and_delimiters[1::2]
    text_and_delimiter_pairs = zip_longest(texts, delimiters)
    start = prediction["start"]

    for text, delimiter in text_and_delimiter_pairs:
        end = start + len(text)

        yield {
            **deepcopy(prediction),
            "text": text,
            "start": start,
            "end": end,
        }

        if delimiter is not None:
            start = end + len(delimiter)
