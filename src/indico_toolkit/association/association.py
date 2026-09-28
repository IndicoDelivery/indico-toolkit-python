from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Union

from ..types import Extractions


class Association(ABC):
    """
    Base class for matching tokens to extraction predictions.
    """

    def __init__(self, predictions: Union[List[dict], Extractions]):
        self._predictions = self.validate_prediction_formatting(predictions)
        self._mapped_positions = []
        self._manually_added_preds = []
        self._errored_predictions = []

    @abstractmethod
    def match_pred_to_token(self):
        pass

    @staticmethod
    def sort_predictions_by_start_index(predictions: List[dict]) -> List[dict]:
        return sorted(predictions, key=lambda x: x["start"])

    @property
    def mapped_positions_by_page(self) -> Dict[int, List[dict]]:
        """
        Return mapped positions by page on which they first appear
        """
        page_map = defaultdict(list)
        for position in self._mapped_positions:
            page_map[position["page_num"]].append(position)
        return page_map

    def validate_prediction_formatting(
        self, predictions: Union[List[dict], Extractions]
    ) -> List[dict]:
        if isinstance(predictions, Extractions):
            predictions = predictions.to_list()
        return predictions

    def _is_manually_added_pred(self, prediction: dict) -> bool:
        return Extractions.is_manually_added_prediction(prediction)


def sequences_overlap(x: dict, y: dict) -> bool:
    """
    Boolean return value indicates whether or not seqs overlap
    """
    return x["start"] < y["end"] and y["start"] < x["end"]


def sequences_exact(x: dict, y: dict) -> bool:
    """
    Boolean return value indicates whether or not seqs are exact
    """
    return x["start"] == y["start"] and x["end"] == y["end"]


def _check_if_token_match_found(pred: dict, no_match_indicator: bool):
    if no_match_indicator:
        pred["error"] = "No matching token found for extraction"
        raise ValueError(f"Couldn't match a token to this prediction:\n{pred}")
