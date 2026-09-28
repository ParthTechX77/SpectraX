from abc import ABC, abstractmethod
from pathlib import Path

import cv2

from app.services.visual.face.schemas import FaceDetection


class FaceAligner(ABC):
    """
    Base interface for face alignment.
    """

    @property
    @abstractmethod
    def aligner_name(self) -> str:
        """Return the alignment implementation name."""

    @property
    @abstractmethod
    def aligner_version(self) -> str:
        """Return the alignment implementation version."""

    @abstractmethod
    def align(
        self,
        *,
        frame_path: str | Path,
        face: FaceDetection,
        output_path: str | Path,
    ) -> Path:
        """
        Crop/alignment of one detected face.

        Returns the path of the aligned face image.
        """
        raise NotImplementedError


class OpenCVFaceCropAligner(FaceAligner):
    """
    Baseline face aligner using the detected bounding box.

    This implementation performs a safe face crop and does not yet
    apply landmark-based geometric normalization.
    """

    @property
    def aligner_name(self) -> str:
        return "opencv_bbox_crop"

    @property
    def aligner_version(self) -> str:
        return cv2.__version__

    def align(
        self,
        *,
        frame_path: str | Path,
        face: FaceDetection,
        output_path: str | Path,
    ) -> Path:
        image = cv2.imread(str(frame_path))

        if image is None:
            raise ValueError(f"Unable to read frame: {frame_path}")

        height, width = image.shape[:2]

        x1 = max(0, min(face.x1, width))
        y1 = max(0, min(face.y1, height))
        x2 = max(0, min(face.x2, width))
        y2 = max(0, min(face.y2, height))

        if x2 <= x1 or y2 <= y1:
            raise ValueError("Invalid face bounding box.")

        face_crop = image[y1:y2, x1:x2]

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if not cv2.imwrite(str(destination), face_crop):
            raise ValueError(f"Unable to write aligned face: {destination}")

        return destination
