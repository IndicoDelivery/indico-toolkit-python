"""Associate row items"""

from collections import defaultdict
from copy import deepcopy
from typing import Iterable, List, Union

from ..types import Extractions
from .association import Association, _check_if_token_match_found, sequences_overlap


class LineItems(Association):
    """
    Class for associating line items given extraction predictions and ondocument OCR
    tokens

    Example Usage:

    litems = LineItems(
            predictions=[{"label": "line_date", "start": 12, "text": "1/2/2021".....}],
            line_item_fields=["line_value", "line_date"],
        )
    litems.get_bounding_boxes(ocr_tokens=[{"postion"...,},])
    litems.assign_row_number()

    # Get your updated predictions
    print(litems.updated_predictions)
    """

    def __init__(
        self,
        predictions: Union[List[dict], Extractions],
        line_item_fields: Iterable[str],
    ):
        """
        Args:
        predictions (List[dict]): List of extraction predictions
        line_item_fields (Iterable[str]): Fields/labels to include as line item values,
            other values will not be assigned a row_number.
        """
        self.predictions = self.validate_prediction_formatting(predictions)
        self.line_item_fields: Iterable[str] = line_item_fields
        self._mapped_positions: List[dict] = []
        self._unmapped_positions: List[dict] = []
        self._errored_predictions: List[dict] = []

    @property
    def updated_predictions(self) -> Extractions:
        return Extractions(
            self._mapped_positions
            + self._unmapped_positions
            + self._errored_predictions
        )

    @staticmethod
    def match_pred_to_token(pred: dict, ocr_tokens: List[dict]):
        """
        Match and add bounding box metadata to prediction.

        Args:
            pred (dict): Indico extraction model prediction
            ocr_tokens (List[dict]): List of OCR tokens

        Raises:
            ValueError: No matching token was found

        Returns:
            [int]: index in ocr tokens where prediction matched
        """
        no_match = True
        match_token_index = 0
        for ind, token in enumerate(ocr_tokens):
            if no_match and sequences_overlap(token["doc_offset"], pred):
                _add_bounding_metadata_to_pred(pred, token)
                no_match = False
                match_token_index = ind
            elif sequences_overlap(token["doc_offset"], pred):
                _update_bounding_metadata_for_pred(pred, token)
            elif token["doc_offset"]["start"] > pred["end"]:
                break
        _check_if_token_match_found(pred, no_match)
        return match_token_index

    def get_bounding_boxes(
        self, ocr_tokens: List[dict], raise_for_no_match: bool = True
    ):
        """
        Adds keys for bounding box top/bottom/left/right and page number to line item
        predictions

        Args:
        ocr_tokens (List[dict]): Tokens from 'ondocument' OCR config output
        raise_for_no_match (bool): raise exception if a matching token isn't found for a
            prediction
        """
        predictions = deepcopy(self.predictions)
        predictions = self._remove_unneeded_predictions(predictions)
        predictions = self.sort_predictions_by_start_index(predictions)
        match_index = 0
        for pred in predictions:
            try:
                match_index = self.match_pred_to_token(pred, ocr_tokens[match_index:])
                self._mapped_positions.append(pred)
            except ValueError as e:
                if raise_for_no_match:
                    raise e
                else:
                    print(f"Ignoring Error: {e}")
                    self._errored_predictions.append(pred)

    def assign_row_number(self):
        """
        Adds a row_number:int key/val pair based on bounding box position and page

        Updates:
        self._mapped_positions (list of dicts): predictions with row_number added
        """
        self._mapped_positions = sorted(
            self._mapped_positions,
            key=lambda x: (x["page_num"], x["bbTop"], x["bbLeft"]),
        )
        starting_pred = self._get_first_valid_line_item_pred()
        max_bot = starting_pred["bbBot"]
        page_number = starting_pred["page_num"]
        row_number = 1
        for pred in self._mapped_positions:
            # if the top of one box equals the bottom of another, we still want a new
            # line
            if pred["bbTop"] >= max_bot or pred["page_num"] != page_number:
                row_number += 1
                page_number = pred["page_num"]
                max_bot = pred["bbBot"]
            else:
                max_bot = max(pred["bbBot"], max_bot)
            pred["row_number"] = row_number

    @property
    def grouped_line_items(self) -> List[List[dict]]:
        """
        After row number has been assigned to predictions, returns line item predictions
        as a list of lists where each list is a row.
        """
        rows = defaultdict(list)
        for pred in self._mapped_positions:
            rows[pred["row_number"]].append(pred)
        return list(rows.values())

    def _remove_unneeded_predictions(self, predictions: List[dict]) -> List[dict]:
        """
        Remove predictions that are not line item fields or don't have valid start/end
        index data
        """
        valid_line_item_preds = []
        for pred in predictions:
            if not self.is_line_item_pred(pred):
                self._unmapped_positions.append(pred)
            elif self._is_manually_added_pred(pred):
                pred["error"] = "Can't match tokens for manually added prediction"
                self._errored_predictions.append(pred)
            else:
                valid_line_item_preds.append(pred)
        return valid_line_item_preds

    def is_line_item_pred(self, pred: dict):
        if pred["label"] in self.line_item_fields:
            return True
        return False

    def _get_first_valid_line_item_pred(self) -> dict:
        if len(self._mapped_positions) == 0:
            raise RuntimeError(
                "Whoops! You have no line_item_fields predictions. "
                "Did you run get_bounding_boxes?"
            )
        return self._mapped_positions[0]


def _add_bounding_metadata_to_pred(pred: dict, token: dict):
    pred["bbTop"] = token["position"]["bbTop"]
    pred["bbBot"] = token["position"]["bbBot"]
    pred["bbLeft"] = token["position"]["bbLeft"]
    pred["bbRight"] = token["position"]["bbRight"]
    pred["page_num"] = token["page_num"]


def _update_bounding_metadata_for_pred(pred: dict, token: dict):
    pred["bbTop"] = min(token["position"]["bbTop"], pred["bbTop"])
    pred["bbBot"] = max(token["position"]["bbBot"], pred["bbBot"])
    pred["bbLeft"] = min(token["position"]["bbLeft"], pred["bbLeft"])
    pred["bbRight"] = max(token["position"]["bbRight"], pred["bbRight"])
