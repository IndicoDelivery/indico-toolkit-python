from typing import List, Union

from ..types import Extractions
from .association import Association, _check_if_token_match_found, sequences_overlap

# TODO: add test that 'errored_predictions' actually works with ValueErrors


class ExtractedTokens(Association):
    """
    Class to collect all extracted tokens, e.g. to enable highlighting of source
    document
    """

    def __init__(self, predictions: Union[List[dict], Extractions]):
        super().__init__(predictions)

    def match_pred_to_token(self, pred: dict, ocr_tokens: List[dict], pred_index: int):
        """
        Append matching token positions to self.mapped_positions, if no matches for
        pred, raise ValueError

        Args:
            pred (dict): Indico extraction model prediction
            ocr_tokens (List[dict]): List of OCR tokens
            pred_index (int): unique number for each prediction so that tokens can be
                linked to it

        Raises:
            ValueError: No matching token was found

        Returns:
            [int]: index in ocr tokens where prediction matched
        """
        no_match = True
        match_token_index = 0
        pred["prediction_index"] = pred_index
        for ind, token in enumerate(ocr_tokens):
            if sequences_overlap(token["doc_offset"], pred):
                self._add_pred_meta_to_token(token, pred, pred_index)
                self._remove_unneeded_token_keys(token)
                self._mapped_positions.append(token)
                match_token_index = ind
                no_match = False
            elif token["doc_offset"]["start"] > pred["end"]:
                break
        _check_if_token_match_found(pred, no_match)
        return match_token_index

    def collect_tokens(self, ocr_tokens: List[dict], raise_for_no_match: bool = True):
        """
        Collect all extracted tokens and with pred text and label added to dictionaries
        Args:
        ocr_tokens (List[dict]): Tokens from 'ondocument' OCR config output
        raise_for_no_match (bool): raise exception if a matching token isn't found for a
            prediction
        """
        self._separate_manually_added_predictions()
        self._predictions = self.sort_predictions_by_start_index(self._predictions)
        match_index = 0
        for pred_ind, pred in enumerate(self._predictions):
            try:
                match_index = self.match_pred_to_token(
                    pred, ocr_tokens[match_index:], pred_ind
                )
            except ValueError as e:
                if raise_for_no_match:
                    raise ValueError(e)
                else:
                    print(f"Ignoring Error: {e}")
                    self._errored_predictions.append(pred)

    @property
    def extracted_tokens(self) -> List[dict]:
        return self._mapped_positions

    @property
    def predictions(self) -> Extractions:
        return Extractions(
            self._predictions + self._errored_predictions + self._manually_added_preds
        )

    @property
    def unmapped_predictions(self) -> Extractions:
        return Extractions(self._errored_predictions + self._manually_added_preds)

    def _remove_unneeded_token_keys(
        self, token: dict, keys: List[str] = ["style", "block_offset", "page_offset"]
    ):
        for key in keys:
            token.pop(key, None)

    def _separate_manually_added_predictions(self):
        predictions = []
        for pred in self._predictions:
            if self._is_manually_added_pred(pred):
                pred["error"] = "Can't match tokens for manually added prediction"
                self._manually_added_preds.append(pred)
            else:
                predictions.append(pred)
        self._predictions = predictions

    def _add_pred_meta_to_token(self, token: dict, pred: dict, pred_index: int):
        token["label"] = pred["label"]
        token["text"] = pred["text"]
        token["prediction_index"] = pred_index
