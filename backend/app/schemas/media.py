from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    original_filename: str
    mime_type: str
    file_size: int
    sha256: str
    description: str | None
    status: str
    created_at: datetime


class MediaVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    media_asset_id: UUID
    version_number: int
    storage_path: str
    sha256: str
    file_size: int
    created_at: datetime


class MediaUploadRead(BaseModel):
    asset: MediaAssetRead
    version: MediaVersionRead
