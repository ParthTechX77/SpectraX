from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class FaceDetection:
    """
    A detected face within a media frame.
    """

    frame_id: UUID

    x1: int
    y1: int
    x2: int
    y2: int

    confidence: float
