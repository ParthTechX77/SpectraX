import json
import subprocess
from decimal import Decimal
from pathlib import Path


class MediaProbeError(Exception):
    """Raised when FFprobe cannot inspect a media file."""


def _to_decimal(value: str | None) -> Decimal | None:
    if value is None or value in {"", "N/A"}:
        return None

    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)

            numerator_decimal = Decimal(numerator)
            denominator_decimal = Decimal(denominator)

            if denominator_decimal == 0:
                return None

            return numerator_decimal / denominator_decimal

        return Decimal(value)

    except (ArithmeticError, ValueError):
        return None


def _to_int(value: str | None) -> int | None:
    if value is None or value in {"", "N/A"}:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def probe_media(path: str | Path) -> dict:
    """
    Run FFprobe against a stored media file.

    Returns normalized metadata plus the complete raw FFprobe response.
    """

    media_path = Path(path)

    if not media_path.is_file():
        raise MediaProbeError(
            f"Media file does not exist: {media_path}"
        )

    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise MediaProbeError(
            "Unable to execute ffprobe."
        ) from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or "Unknown ffprobe error"
        raise MediaProbeError(
            f"FFprobe failed: {detail}"
        )

    try:
        probe_data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise MediaProbeError(
            "FFprobe returned invalid JSON."
        ) from exc

    streams = probe_data.get("streams", [])
    format_data = probe_data.get("format", {})

    video_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "video"),
        None,
    )

    audio_stream = next(
        (stream for stream in streams if stream.get("codec_type") == "audio"),
        None,
    )

    if video_stream:
        media_type = "video"
    elif audio_stream:
        media_type = "audio"
    else:
        media_type = "unknown"

    return {
        "media_type": media_type,
        "duration_seconds": _to_decimal(
            format_data.get("duration")
        ),
        "width": _to_int(
            video_stream.get("width") if video_stream else None
        ),
        "height": _to_int(
            video_stream.get("height") if video_stream else None
        ),
        "frame_rate": _to_decimal(
            video_stream.get("avg_frame_rate")
            if video_stream
            else None
        ),
        "video_codec": (
            video_stream.get("codec_name")
            if video_stream
            else None
        ),
        "audio_codec": (
            audio_stream.get("codec_name")
            if audio_stream
            else None
        ),
        "audio_sample_rate": _to_int(
            audio_stream.get("sample_rate")
            if audio_stream
            else None
        ),
        "audio_channels": _to_int(
            audio_stream.get("channels")
            if audio_stream
            else None
        ),
        "probe_data": probe_data,
    }
