from abc import ABC, abstractmethod

import torch

from app.services.visual.classifier.schemas import ClassificationResult


class DeepfakeClassifier(ABC):
    """
    Base interface for deepfake classification heads.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the classifier name."""

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return the classifier version."""

    @abstractmethod
    def classify(self, features: torch.Tensor) -> ClassificationResult:
        """
        Convert visual features into a frame-level manipulation signal.
        """
        raise NotImplementedError
