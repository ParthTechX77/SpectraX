from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from app.services.visual.schemas import VisualDetectionResult


class VisualDetector(ABC):
    """
    Base interface for frame-level visual deepfake detectors.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the detector model name."""

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return the detector model version."""

    @abstractmethod
    def detect(
        self,
        *,
        frame_id: UUID,
        frame_path: str | Path,
        timestamp_seconds: float,
    ) -> VisualDetectionResult:
        """
        Analyze one frame and return a visual detection result.
        """
        raise NotImplementedError
