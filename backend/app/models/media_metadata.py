import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MediaMetadata(Base):
    __tablename__ = "media_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    media_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    media_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    duration_seconds: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 6),
        nullable=True,
    )

    width: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    height: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    frame_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 6),
        nullable=True,
    )

    video_codec: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    audio_codec: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    audio_sample_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    audio_channels: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    probe_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    media_asset = relationship(
        "MediaAsset",
        back_populates="media_metadata",
    )
