from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.services.case_service import (
    create_case,
    get_case,
    list_cases,
    update_case,
)


router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


@router.post(
    "",
    response_model=CaseRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_case_endpoint(
    data: CaseCreate,
    db: AsyncSession = Depends(get_db),
):
    return await create_case(db, data)


@router.get(
    "",
    response_model=list[CaseRead],
)
async def list_cases_endpoint(
    db: AsyncSession = Depends(get_db),
):
    return await list_cases(db)


@router.get(
    "/{case_id}",
    response_model=CaseRead,
)
async def get_case_endpoint(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return case

@router.patch(
    "/{case_id}",
    response_model=CaseRead,
)
async def update_case_endpoint(
    case_id: UUID,
    data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    try:
        case = await update_case(db, case_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return case