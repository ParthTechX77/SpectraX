from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VisualDetectionResult:
    """
    Result produced by a visual deepfake detector for one frame.
    """

    frame_id: UUID
    timestamp_seconds: float
    score: float
    model_name: str
    model_version: str
    face_detected: bool
    processing_time_ms: float | None = None
