from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_frame import MediaFrame
from app.services.visual.detection_service import (
    get_existing_visual_detection,
    save_visual_detection,
)
from app.services.visual.detector import VisualDetector
from app.services.visual.schemas import VisualDetectionResult
from app.storage.local import LocalStorage


class MultiFrameVisualAnalysisService:
    """
    Run a frame-level visual detector across all frames of one media asset.
    """

    def __init__(
        self,
        *,
        detector: VisualDetector,
        storage: LocalStorage,
    ) -> None:
        self.detector = detector
        self.storage = storage

    async def analyze_asset(
        self,
        *,
        db: AsyncSession,
        media_asset_id: UUID,
    ) -> list[VisualDetectionResult]:
        result = await db.execute(
            select(MediaFrame)
            .where(MediaFrame.media_asset_id == media_asset_id)
            .order_by(MediaFrame.frame_number.asc())
        )

        frames = result.scalars().all()

        if not frames:
            return []

        results: list[VisualDetectionResult] = []

        for frame in frames:
            if not self.storage.exists(frame.storage_path):
                raise FileNotFoundError(
                    f"Frame file not found: {frame.storage_path}"
                )

            frame_path = self.storage.resolve_path(frame.storage_path)

            detection_result = self.detector.detect(
                frame_id=frame.id,
                frame_path=frame_path,
                timestamp_seconds=float(frame.timestamp_seconds),
            )

            existing = await get_existing_visual_detection(
                db,
                detection_result,
            )

            if existing is None:
                await save_visual_detection(
                    db,
                    detection_result,
                )

            results.append(detection_result)

        return results
