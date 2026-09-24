from typing import List

from .predictions import Predictions


class WorkflowResult:
    def __init__(self, result: dict, model_name: str | None = None):
        """
        Common functionality for workflow result object

        Args:
            result (dict): raw workflow result object
            model_name (str, optional): Extraction/Classification model name.
                Defaults to None.
        """
        self.result = result
        self.model_name = model_name

    def _check_is_valid_model_name(self) -> None:
        if self.model_name not in self.available_model_names:
            raise KeyError(
                f"{self.model_name} is not an available model name. "
                f"Options: {self.available_model_names}"
            )

    def __repr__(self):
        return f"WorkflowResult object, Submission ID: {self.submission_id}"

    @property
    def get_predictions(self) -> Predictions:
        """
        Return predictions without human review
        """
        self._set_model_name()
        preds = self.document_results[self.model_name]
        if "pre_review" in preds:
            preds = preds["pre_review"]
        return Predictions.get_obj(preds)

    @property
    def pre_review_predictions(self) -> Predictions:
        """
        Return predictions before human review
        """
        self._set_model_name()
        preds = self.document_results[self.model_name]
        if "pre_review" in preds:
            preds = preds["pre_review"]
            return Predictions.get_obj(preds)
        else:
            return Predictions.get_obj([])

    @property
    def post_reviews_predictions(self) -> Predictions:
        """
        Return predictions after human review
        """
        self._set_model_name()
        preds = self.document_results[self.model_name]
        if "post_reviews" in preds:
            post_review_preds = []
            reviews = preds["post_reviews"]
            for review in reviews:
                post_review_preds.append(Predictions.get_obj(review))
            return post_review_preds  # type: ignore[ty:invalid-return-type]
        else:
            return Predictions.get_obj([])

    @property
    def final_predictions(self) -> Predictions:
        self._set_model_name()
        preds = self.document_results[self.model_name]
        if "final" in preds:
            preds = preds["final"]
            return Predictions.get_obj(preds)
        else:
            return Predictions.get_obj([])

    def _set_model_name(self):
        """
        Attempts to select the relevant model name if not already specified.
        Raises error if multiple models are available and self.model_name specified.
        """
        if self.model_name:
            self._check_is_valid_model_name()
        elif len(self.available_model_names) > 1:
            raise RuntimeError(
                "Multiple models available, you must set self.model_name to one of "
                f"{self.available_model_names}"
            )
        else:
            self.model_name = self.available_model_names[0]

    @property
    def etl_url(self) -> str:
        return self.result["etl_output"]

    @property
    def document_results(self) -> dict:
        return self.result["results"]["document"]["results"]

    @property
    def available_model_names(self) -> List[str]:
        return list(self.document_results.keys())

    @property
    def submission_id(self) -> str:
        return self.result["submission_id"]

    @property
    def errors(self) -> list:
        return self.result["errors"]

    @property
    def review_id(self) -> int:
        return self.result["review_id"]

    @property
    def reviewer_id(self) -> int:
        return self.result["reviewer_id"]

    @property
    def review_notes(self) -> int:
        return self.result["review_notes"]

    @property
    def review_rejected(self) -> int:
        return self.result["review_rejected"]

    @property
    def admin_review(self) -> bool:
        return self.result["admin_review"]
