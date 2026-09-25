from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MediaFrame


async def create_media_frames(
    db: AsyncSession,
    *,
    media_asset_id: UUID,
    frames: list[dict],
) -> list[MediaFrame]:
    """
    Persist extracted frame metadata for a media asset.
    """

    media_frames = [
        MediaFrame(
            media_asset_id=media_asset_id,
            frame_number=frame["frame_number"],
            timestamp_seconds=frame["timestamp_seconds"],
            storage_path=frame["storage_path"],
            width=frame.get("width"),
            height=frame.get("height"),
        )
        for frame in frames
    ]

    db.add_all(media_frames)

    await db.flush()

    return media_frames
