from pathlib import Path


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".m4v",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".m4a",
    ".ogg",
}


def validate_media_identity(
    *,
    filename: str,
    declared_mime: str | None,
    detected_media_type: str,
) -> str:
    """
    Validate the relationship between filename, declared MIME,
    and FFprobe-detected media type.

    The detected media type is authoritative for the actual
    media content; the filename and declared MIME are treated
    as metadata that must be consistent enough for ingestion.
    """

    extension = Path(filename).suffix.lower()

    if detected_media_type == "video":
        allowed_extensions = VIDEO_EXTENSIONS

        if extension not in allowed_extensions:
            raise ValueError(
                f"Video content has unsupported file extension: {extension or 'none'}"
            )

        if declared_mime:
            if not (
                declared_mime.startswith("video/")
                or declared_mime == "application/octet-stream"
            ):
                raise ValueError(
                    f"Declared MIME type '{declared_mime}' "
                    "does not match detected video content."
                )

        return "video"

    if detected_media_type == "audio":
        allowed_extensions = AUDIO_EXTENSIONS

        if extension not in allowed_extensions:
            raise ValueError(
                f"Audio content has unsupported file extension: {extension or 'none'}"
            )

        if declared_mime:
            if not (
                declared_mime.startswith("audio/")
                or declared_mime == "application/octet-stream"
            ):
                raise ValueError(
                    f"Declared MIME type '{declared_mime}' "
                    "does not match detected audio content."
                )

        return "audio"

    raise ValueError(
        f"Unsupported detected media type: {detected_media_type}"
    )
