from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from app.models.case import CaseStatus

class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: CaseStatus | None = None

class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_number: str
    title: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime