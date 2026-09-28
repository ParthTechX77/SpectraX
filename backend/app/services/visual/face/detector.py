from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

import cv2

from app.services.visual.face.schemas import FaceDetection


class FaceDetector(ABC):
    """
    Base interface for face detectors.
    """

    @property
    @abstractmethod
    def detector_name(self) -> str:
        """Return the face detector name."""

    @property
    @abstractmethod
    def detector_version(self) -> str:
        """Return the face detector version."""

    @abstractmethod
    def detect(
        self,
        *,
        frame_id: UUID,
        frame_path: str | Path,
    ) -> list[FaceDetection]:
        """
        Detect faces in one frame.
        """
        raise NotImplementedError


class OpenCVHaarFaceDetector(FaceDetector):
    """
    Lightweight baseline face detector using OpenCV Haar Cascade.
    """

    def __init__(
        self,
        *,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_size: tuple[int, int] = (40, 40),
    ) -> None:
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(cascade_path)

        if self._cascade.empty():
            raise RuntimeError("Failed to load OpenCV Haar face cascade.")

    @property
    def detector_name(self) -> str:
        return "opencv_haar"

    @property
    def detector_version(self) -> str:
        return cv2.__version__

    def detect(
        self,
        *,
        frame_id: UUID,
        frame_path: str | Path,
    ) -> list[FaceDetection]:
        image = cv2.imread(str(frame_path))

        if image is None:
            raise ValueError(f"Unable to read frame: {frame_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detections = self._cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size,
        )

        results: list[FaceDetection] = []

        for x, y, width, height in detections:
            results.append(
                FaceDetection(
                    frame_id=frame_id,
                    x1=int(x),
                    y1=int(y),
                    x2=int(x + width),
                    y2=int(y + height),
                    confidence=1.0,
                )
            )

        return results
