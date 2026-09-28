from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationResult:
    """
    Frame-level output from a deepfake classification model.

    The score is a model-specific manipulation signal and must not
    automatically be interpreted as a calibrated probability.
    """

    score: float
    label: str
    model_name: str
    model_version: str
