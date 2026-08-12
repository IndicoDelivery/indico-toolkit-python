import csv
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, List, Set, Union

from ..errors import ToolkitInputError


class Extractions:
    """
    Functionality for common extraction prediction use cases
    """

    def __init__(self, predictions: List[dict]):
        self._preds = predictions
        self.removed_predictions = []

    @property
    def to_dict_by_label(self) -> Dict[str, list]:
        """
        Generate a dictionary where key is label string and value is list of all
        predictions of that label
        """
        prediction_label_map = defaultdict(list)
        for pred in self._preds:
            prediction_label_map[pred["label"]].append(pred)
        return prediction_label_map

    @property
    def num_predictions(self) -> int:
        return len(self._preds)

    def remove_by_confidence(self, confidence: float = 0.95, labels: List[str] = None):
        """
        Remove predictions that are less than given confidence
        Args:
            confidence (float, optional): confidence theshold. Defaults to 0.95.
            labels (List[str], optional): Labels where this applies,
                if None applies to all. Defaults to None.
        """
        high_conf_preds = []
        for pred in self._preds:
            label = pred["label"]
            if labels and label not in labels:
                high_conf_preds.append(pred)
            elif pred["confidence"][label] >= confidence:
                high_conf_preds.append(pred)
            else:
                self.removed_predictions.append(pred)
        self._preds = high_conf_preds

    def remove_except_max_confidence(self, labels: List[str]):
        """
        Removes all predictions except the highest confidence within each specified
        class
        """
        label_set = self.label_set
        for label in labels:
            if label not in label_set:
                continue
            max_pred = self._select_max_confidence(label)
            self.remove_all_by_label([label])
            self.removed_predictions.remove(max_pred)
            self._preds.append(max_pred)

    def set_confidence_key_to_max_value(self, inplace: bool = True):
        """
        Overwite confidence dictionary to just max confidence float to make preds more
        readable.
        """
        if inplace:
            self._set_confidence_key_to_max_value(self._preds)
        else:
            return self._set_confidence_key_to_max_value(deepcopy(self._preds))

    @staticmethod
    def _set_confidence_key_to_max_value(preds):
        for pred in preds:
            pred["confidence"] = pred["confidence"][pred["label"]]
        return preds

    def remove_keys(self, keys_to_remove: List[str] = ["start", "end"]):
        """
        Remove specified keys from prediction dictionaries
        """
        for pred in self._preds:
            for key in keys_to_remove:
                pred.pop(key)

    def remove_all_by_label(self, labels: Iterable[str]):
        """
        Remove all predictions in list of labels
        """
        preds = []
        for p in self._preds:
            if p["label"] in labels:
                self.removed_predictions.append(p)
            else:
                preds.append(p)
        self._preds = preds

    def remove_human_added_predictions(self):
        """
        Remove predictions that were not added by the model (i.e. added by scripted or
        human review)
        """
        self._preds = [
            i for i in self._preds if not self.is_manually_added_prediction(i)
        ]

    def to_list(self):
        return self._preds

    @staticmethod
    def is_manually_added_prediction(prediction: dict) -> bool:
        if isinstance(prediction["start"], int) and isinstance(prediction["end"], int):
            if prediction["end"] > prediction["start"]:
                return False
        return True

    @staticmethod
    def get_label_set(predictions: List[dict]) -> Set[str]:
        """
        Get the included labels from a list of predictions
        """
        return set([i["label"] for i in predictions])

    def get_text_values(self, label: str) -> List[str]:
        """
        Get all text values for a given label
        """
        return [i["text"] for i in self._preds if i["label"] == label]

    @property
    def label_set(self):
        return self.get_label_set(self._preds)

    def _select_max_confidence(self, label: str) -> dict:
        """
        Get the highest confidence prediction for a given field
        """
        max_pred = None
        confidence = 0
        for pred in self[label]:
            pred_confidence = pred["confidence"][label]
            if pred_confidence >= confidence:
                max_pred = pred
                confidence = pred_confidence
        return max_pred

    @property
    def label_count_dict(self) -> Dict[str, int]:
        """
        Get count of occurrences of each label
        """
        return dict(Counter(i["label"] for i in self._preds))

    def exist_multiple_vals_for_label(self, label: str) -> bool:
        """
        Check whether multiple unique text vals for field
        """
        if len(set(self.get_text_values(label))) > 1:
            return True
        return False

    def get_most_common_text_value(self, label: str) -> Union[str, None]:
        """
        Return the most common text value. If there is a tie- returns None.
        """
        if label not in self.label_set:
            raise ToolkitInputError(f"There are no predictions for: '{label}'")
        text_vals = self.get_text_values(label)
        if len(set(text_vals)) == 1:
            return text_vals[0]
        most_common = Counter(text_vals).most_common(2)
        if most_common[0][1] > most_common[1][1]:
            return most_common[0][0]
        return None

    def __len__(self):
        return len(self._preds)

    def __repr__(self):
        return f"{self.num_predictions} Extractions:\n\n{self._preds}"

    def __getitem__(self, label: str) -> List[dict]:
        return [i for i in self._preds if i["label"] == label]

    def to_csv(
        self,
        save_path: str,
        filename: str = "",
        append_if_exists: bool = True,
        include_start_end: bool = False,
    ) -> None:
        """
        Write three column CSV ('confidence', 'label', 'text')
        Args:
            save_path (str): path to write CSV
            include_start_end (bool): include columns for start/end indexes
            append_if_exists (bool): if path exists, append to that CSV
            filename (str, optional): the file where the preds were derived from.
                Defaults to "".
        """
        preds = self.set_confidence_key_to_max_value(inplace=False)

        for pred in preds:
            if not include_start_end:
                pred.pop("start", None)
                pred.pop("end", None)

            pred["filename"] = filename

        fieldnames: List[str] = []

        for pred in preds:
            for key in pred:
                if key not in fieldnames:
                    fieldnames.append(key)

        append = append_if_exists and Path(save_path).exists()
        mode = "a" if append else "w"

        with open(save_path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not append:
                writer.writeheader()

            writer.writerows(preds)
