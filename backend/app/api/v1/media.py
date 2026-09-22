from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.media import MediaUploadRead
from app.services.case_service import get_case
from app.services.media_service import ingest_media


router = APIRouter(
    prefix="/cases/{case_id}/media",
    tags=["Media"],
)


@router.post(
    "",
    response_model=MediaUploadRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_media(
    case_id: UUID,
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    try:
        asset, version = await ingest_media(
            db,
            case_id=case_id,
            upload=file,
            description=description,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "asset": asset,
        "version": version,
    }
