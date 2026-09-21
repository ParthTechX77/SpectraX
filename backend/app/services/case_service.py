import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Case
from app.schemas.case import CaseCreate


def generate_case_number() -> str:
    return f"SPX-{uuid.uuid4().hex[:12].upper()}"


async def create_case(
    db: AsyncSession,
    data: CaseCreate,
) -> Case:
    case = Case(
        case_number=generate_case_number(),
        title=data.title,
        description=data.description,
    )

    db.add(case)
    await db.commit()
    await db.refresh(case)

    return case


async def list_cases(
    db: AsyncSession,
) -> list[Case]:
    result = await db.execute(
        select(Case).order_by(Case.created_at.desc())
    )

    return list(result.scalars().all())


async def get_case(
    db: AsyncSession,
    case_id: uuid.UUID,
) -> Case | None:
    result = await db.execute(
        select(Case).where(Case.id == case_id)
    )

    return result.scalar_one_or_none()
