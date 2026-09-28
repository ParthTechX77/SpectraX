from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.visual_detection import VisualDetection
from app.services.visual.schemas import VisualDetectionResult


async def get_existing_visual_detection(
    db: AsyncSession,
    result: VisualDetectionResult,
) -> VisualDetection | None:
    query = await db.execute(
        select(VisualDetection)
        .where(
            VisualDetection.media_frame_id == result.frame_id,
            VisualDetection.model_name == result.model_name,
            VisualDetection.model_version == result.model_version,
        )
    )

    return query.scalar_one_or_none()


async def save_visual_detection(
    db: AsyncSession,
    result: VisualDetectionResult,
) -> VisualDetection:
    detection = VisualDetection(
        media_frame_id=result.frame_id,
        score=Decimal(str(result.score)),
        model_name=result.model_name,
        model_version=result.model_version,
        face_detected=result.face_detected,
        processing_time_ms=(
            Decimal(str(result.processing_time_ms))
            if result.processing_time_ms is not None
            else None
        ),
    )

    db.add(detection)
    await db.flush()

    return detection
