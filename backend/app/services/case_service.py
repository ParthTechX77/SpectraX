import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Case
from app.models.case import CaseStatus
from app.schemas.case import CaseCreate, CaseUpdate
from app.services.audit_service import create_audit_log

ALLOWED_STATUS_TRANSITIONS = {
    CaseStatus.CREATED: {
        CaseStatus.IN_PROGRESS,
    },
    CaseStatus.IN_PROGRESS: {
        CaseStatus.COMPLETED,
    },
    CaseStatus.COMPLETED: {
        CaseStatus.ARCHIVED,
    },
    CaseStatus.ARCHIVED: set(),
}

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

    await db.flush()

    await create_audit_log(
        db,
        action="CASE_CREATED",
        case_id=case.id,
        description="Investigation case created.",
        details={
            "case_number": case.case_number,
            "title": case.title,
        },
    )

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


async def update_case(
    db: AsyncSession,
    case_id: uuid.UUID,
    data: CaseUpdate,
) -> Case | None:
    case = await get_case(db, case_id)

    if case is None:
        return None

    changes = data.model_dump(exclude_unset=True)

    if not changes:
        return case

    if "status" in changes:
        current_status = CaseStatus(case.status)
        new_status = changes["status"]

        if new_status != current_status:
            allowed_statuses = ALLOWED_STATUS_TRANSITIONS[current_status]

            if new_status not in allowed_statuses:
                raise ValueError(
                    f"Invalid status transition: "
                    f"{current_status.value} -> {new_status.value}"
                )

        changes["status"] = new_status.value


    old_values = {
        field: getattr(case, field)
        for field in changes
    }

    for field, value in changes.items():
        setattr(case, field, value)

    await db.flush()

    await create_audit_log(
        db,
        action="CASE_UPDATED",
        case_id=case.id,
        description="Investigation case updated.",
        details={
            "changes": changes,
            "previous_values": old_values,
        },
    )

    await db.commit()
    await db.refresh(case)

    return case