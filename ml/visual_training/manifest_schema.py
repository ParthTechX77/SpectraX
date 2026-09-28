from dataclasses import dataclass


@dataclass(frozen=True)
class VisualSample:
    sample_id: str
    source_video_id: str
    frame_number: int
    frame_path: str

    label: int
    manipulation_type: str
    split: str

    timestamp_seconds: float

    face_index: int
    face_x1: int
    face_y1: int
    face_x2: int
    face_y2: int


VALID_LABELS = {0, 1}
VALID_SPLITS = {"train", "val", "test"}


def validate_sample(sample: VisualSample) -> None:
    if sample.label not in VALID_LABELS:
        raise ValueError(f"Invalid label: {sample.label}")

    if sample.split not in VALID_SPLITS:
        raise ValueError(f"Invalid split: {sample.split}")

    if sample.frame_number < 1:
        raise ValueError("frame_number must be >= 1")

    if sample.timestamp_seconds < 0:
        raise ValueError("timestamp_seconds must be >= 0")

    if sample.face_index < 0:
        raise ValueError("face_index must be >= 0")

    if sample.face_x2 <= sample.face_x1:
        raise ValueError("Invalid face x coordinates")

    if sample.face_y2 <= sample.face_y1:
        raise ValueError("Invalid face y coordinates")
