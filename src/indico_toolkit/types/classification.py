import csv
from operator import itemgetter
from pathlib import Path
from typing import Dict


class Classification:
    """
    Functionality for classification predictions
    """

    def __init__(self, prediction: dict):
        self._pred = prediction

    @property
    def label(self) -> str:
        return self._pred["label"]

    @property
    def labels(self) -> list:
        return list(self.confidence_scores.keys())

    @property
    def confidence(self) -> float:
        return self.confidence_scores[self.label]

    def set_confidence_key_to_max_value(self):
        """
        Overwite confidence dictionary to just max confidence float
        """
        self._pred["confidence"] = self._pred["confidence"][self.label]

    @property
    def confidence_scores(self) -> Dict[str, float]:
        return self._pred["confidence"]

    def to_csv(
        self, save_path, filename: str = "", append_if_exists: bool = True
    ) -> None:
        row = dict(self._pred)
        row["filename"] = filename
        fieldnames = list(row.keys())
        append = append_if_exists and Path(save_path).exists()
        mode = "a" if append else "w"

        with open(save_path, mode, newline="") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            if not append:
                csv_writer.writeheader()

            csv_writer.writerow(row)


class ClassificationMGP(Classification):
    """
    Classification wrapper to account for
    ModelGroupPredict returning a varied json output compared with Workflow

    EXAMPLE:::
        {'Type A': 0.99, 'Type B': 0.01}
    """

    @property
    def label(self) -> str:
        return max(self._pred.items(), key=itemgetter(1))[0]

    @property
    def labels(self) -> list:
        return list(self._pred.keys())

    @property
    def confidence(self) -> float:
        return self._pred[self.label]

    def set_confidence_key_to_max_value(self):
        """
        Overwite confidence dictionary to just max confidence float
        """
        self._pred["confidence"] = self.confidence

    @property
    def confidence_scores(self) -> Dict[str, float]:
        return self._pred
