import subprocess
from pathlib import Path
from uuid import UUID

from PIL import Image

from app.storage.local import LocalStorage


class FrameExtractionError(Exception):
    """Raised when frame extraction fails."""


def extract_frames(
    *,
    media_path: str | Path,
    media_asset_id: UUID,
    sample_fps: float = 1.0,
) -> list[dict]:
    """
    Extract sampled JPEG frames from a video using FFmpeg.
    Returns metadata for every extracted frame.
    """

    if sample_fps <= 0:
        raise ValueError("sample_fps must be greater than zero.")

    source = Path(media_path)

    if not source.is_file():
        raise FrameExtractionError(
            f"Media file does not exist: {source}"
        )

    storage = LocalStorage()

    output_directory = (
        storage.directories["extracted"] / str(media_asset_id)
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_pattern = output_directory / "frame_%06d.jpg"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vf",
        f"fps={sample_fps}",
        "-q:v",
        "2",
        str(output_pattern),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise FrameExtractionError(
            "Unable to execute ffmpeg."
        ) from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or "Unknown FFmpeg error"
        raise FrameExtractionError(
            f"FFmpeg frame extraction failed: {detail}"
        )

    extracted_files = sorted(
        output_directory.glob("frame_*.jpg")
    )

    if not extracted_files:
        raise FrameExtractionError(
            "FFmpeg completed but produced no frames."
        )

    frames: list[dict] = []

    for frame_number, frame_path in enumerate(
        extracted_files,
        start=1,
    ):
        timestamp_seconds = (
            frame_number - 1
        ) / sample_fps

        try:
            with Image.open(frame_path) as image:
                width, height = image.size
        except OSError as exc:
            raise FrameExtractionError(
                f"Unable to read extracted frame: {frame_path}"
            ) from exc

        frames.append(
            {
                "frame_number": frame_number,
                "timestamp_seconds": timestamp_seconds,
                "storage_path": str(
                    frame_path.relative_to(storage.base_path)
                ),
                "width": width,
                "height": height,
            }
        )

    return frames
