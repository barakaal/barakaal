from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schema
# ---------------------------------------------------------------------------

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_type: str
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: object  # datetime


# ---------------------------------------------------------------------------
# Paginated response reuse
# ---------------------------------------------------------------------------

from app.schemas.common import PaginatedResponse


@router.get("/", response_model=PaginatedResponse[AuditLogOut], summary="List audit logs")
async def list_audit_logs(
    actor_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> PaginatedResponse[AuditLogOut]:
    base_query = select(AuditLog)
    if actor_type:
        base_query = base_query.where(AuditLog.actor_type == actor_type)
    if entity_type:
        base_query = base_query.where(AuditLog.entity_type == entity_type)
    if date_from:
        base_query = base_query.where(func.date(AuditLog.created_at) >= date_from)
    if date_to:
        base_query = base_query.where(func.date(AuditLog.created_at) <= date_to)

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[AuditLogOut.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{log_id}", response_model=AuditLogOut, summary="Get audit log entry by ID")
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> AuditLogOut:
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log entry not found")
    return AuditLogOut.model_validate(log)
