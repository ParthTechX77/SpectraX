import hashlib
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MediaAsset, MediaMetadata, MediaVersion
from app.services.audit_service import create_audit_log
from app.services.frame_extraction_service import (
    FrameExtractionError,
    extract_frames,
)
from app.services.media_frame_service import create_media_frames
from app.services.media_probe_service import (
    MediaProbeError,
    probe_media,
)
from app.services.media_validation_service import (
    validate_media_identity,
)
from app.storage.local import LocalStorage


async def ingest_media(
    db: AsyncSession,
    *,
    case_id: uuid.UUID,
    upload: UploadFile,
    description: str | None = None,
):
    # ---------------------------------------------------------
    # 1. Read uploaded file
    # ---------------------------------------------------------
    data = await upload.read()

    if not data:
        raise ValueError("Uploaded file is empty.")

    file_size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()

    filename = upload.filename or "unnamed"

    declared_mime = (
        upload.content_type
        or "application/octet-stream"
    )

    # ---------------------------------------------------------
    # 2. Save original evidence file
    # ---------------------------------------------------------
    storage = LocalStorage()

    storage_path = storage.save_bytes(
        data=data,
        category="uploads",
        filename=filename,
    )

    stored_file = storage.base_path / storage_path

    try:
        # -----------------------------------------------------
        # 3. Probe actual media content with FFprobe
        # -----------------------------------------------------
        try:
            metadata = probe_media(stored_file)

        except MediaProbeError as exc:
            storage.delete(storage_path)

            raise ValueError(
                f"Invalid or unsupported media file: {exc}"
            ) from exc

        # -----------------------------------------------------
        # 4. Ensure FFprobe detected a supported media type
        # -----------------------------------------------------
        if metadata["media_type"] == "unknown":
            storage.delete(storage_path)

            raise ValueError(
                "Unable to determine media type."
            )

        # -----------------------------------------------------
        # 5. Validate filename + declared MIME +
        #    detected media content
        # -----------------------------------------------------
        try:
            validated_media_type = validate_media_identity(
                filename=filename,
                declared_mime=declared_mime,
                detected_media_type=metadata["media_type"],
            )

        except ValueError as exc:
            storage.delete(storage_path)

            raise ValueError(str(exc)) from exc

        # -----------------------------------------------------
        # 6. Create MediaAsset
        # -----------------------------------------------------
        asset = MediaAsset(
            case_id=case_id,
            original_filename=filename,
            mime_type=declared_mime,
            file_size=file_size,
            sha256=sha256,
            description=description,
        )

        db.add(asset)
        await db.flush()

        # -----------------------------------------------------
        # 7. Create MediaVersion
        # -----------------------------------------------------
        version = MediaVersion(
            media_asset_id=asset.id,
            version_number=1,
            storage_path=storage_path,
            sha256=sha256,
            file_size=file_size,
        )

        db.add(version)

        # -----------------------------------------------------
        # 8. Persist probed media metadata
        # -----------------------------------------------------
        media_metadata = MediaMetadata(
            media_asset_id=asset.id,
            media_type=validated_media_type,
            duration_seconds=metadata["duration_seconds"],
            width=metadata["width"],
            height=metadata["height"],
            frame_rate=metadata["frame_rate"],
            video_codec=metadata["video_codec"],
            audio_codec=metadata["audio_codec"],
            audio_sample_rate=metadata["audio_sample_rate"],
            audio_channels=metadata["audio_channels"],
            probe_data=metadata["probe_data"],
        )

        db.add(media_metadata)

        # -----------------------------------------------------
        # 9. Extract and persist video frames
        # -----------------------------------------------------
        if validated_media_type == "video":
            try:
                frames = extract_frames(
                    media_path=stored_file,
                    media_asset_id=asset.id,
                    sample_fps=1.0,
                )

                await create_media_frames(
                    db,
                    media_asset_id=asset.id,
                    frames=frames,
                )

            except FrameExtractionError as exc:
                await db.rollback()
                storage.delete(storage_path)

                raise ValueError(
                    f"Frame extraction failed: {exc}"
                ) from exc

        # -----------------------------------------------------
        # 10. Create audit log
        # -----------------------------------------------------
        await create_audit_log(
            db,
            action="media_ingested",
            description="Media uploaded and ingested.",
            case_id=case_id,
            details={
                "media_asset_id": str(asset.id),
                "media_version_id": str(version.id),
                "original_filename": filename,
                "mime_type": declared_mime,
                "file_size": file_size,
                "sha256": sha256,
                "storage_path": storage_path,
                "media_type": validated_media_type,
                "duration_seconds": (
                    str(metadata["duration_seconds"])
                    if metadata["duration_seconds"] is not None
                    else None
                ),
                "width": metadata["width"],
                "height": metadata["height"],
                "frame_rate": (
                    str(metadata["frame_rate"])
                    if metadata["frame_rate"] is not None
                    else None
                ),
                "video_codec": metadata["video_codec"],
                "audio_codec": metadata["audio_codec"],
                "audio_sample_rate": metadata["audio_sample_rate"],
                "audio_channels": metadata["audio_channels"],
            },
        )

        # -----------------------------------------------------
        # 11. Commit complete ingestion transaction
        # -----------------------------------------------------
        await db.commit()

        await db.refresh(asset)
        await db.refresh(version)

        return asset, version

    except ValueError:
        # ValueError paths already clean up the stored file
        # where appropriate.
        raise

    except Exception:
        # Any unexpected DB/application failure must not leave
        # the uploaded evidence file orphaned.
        await db.rollback()
        storage.delete(storage_path)
        raise
