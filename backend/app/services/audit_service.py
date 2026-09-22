import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def create_audit_log(
    db: AsyncSession,
    *,
    action: str,
    case_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    description: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        case_id=case_id,
        action=action,
        description=description,
        details=details,
    )

    db.add(audit_log)
    await db.flush()

    return audit_log
