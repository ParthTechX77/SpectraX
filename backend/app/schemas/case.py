from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_number: str
    title: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
