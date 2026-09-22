import hashlib
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MediaAsset, MediaVersion
from app.services.audit_service import create_audit_log
from app.storage.local import LocalStorage


async def ingest_media(
    db: AsyncSession,
    *,
    case_id: uuid.UUID,
    upload: UploadFile,
    description: str | None = None,
) -> tuple[MediaAsset, MediaVersion]:

    data = await upload.read()

    if not data:
        raise ValueError("Uploaded file is empty")

    file_size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()

    filename = upload.filename or "unnamed"

    storage = LocalStorage()

    storage_path = storage.save_bytes(
        data=data,
        category="uploads",
        filename=filename,
    )

    asset = MediaAsset(
        case_id=case_id,
        original_filename=filename,
        mime_type=upload.content_type or "application/octet-stream",
        file_size=file_size,
        sha256=sha256,
        description=description,
        status="ingested",
    )

    db.add(asset)
    await db.flush()

    version = MediaVersion(
        media_asset_id=asset.id,
        version_number=1,
        storage_path=storage_path,
        sha256=sha256,
        file_size=file_size,
    )

    db.add(version)

    await create_audit_log(
        db,
        action="MEDIA_UPLOADED",
        case_id=case_id,
        description="Media evidence uploaded and ingested.",
        details={
            "media_asset_id": str(asset.id),
            "media_version_id": str(version.id),
            "original_filename": filename,
            "mime_type": upload.content_type or "application/octet-stream",
            "file_size": file_size,
            "sha256": sha256,
            "storage_path": storage_path,
        },
    )

    await db.commit()

    await db.refresh(asset)
    await db.refresh(version)

    return asset, version
