from .classification import Classification, ClassificationMGP
from .extractions import Extractions


class Predictions:
    """
    Factory class for predictions
    """

    @staticmethod
    def get_obj(predictions):
        """
        Returns:
        Extractions object or Classification object depending on predictions type
        """
        if isinstance(predictions, list):
            return Extractions(predictions)
        elif isinstance(predictions, dict):
            if "label" in predictions:
                return Classification(predictions)
            else:
                return ClassificationMGP(predictions)
        else:
            raise TypeError(
                f"Unable to process predictions with type {type(predictions)}. "
                f"Predictions: {predictions}"
            )
