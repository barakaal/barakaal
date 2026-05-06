from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.agent import AgentDecision, DecisionStatus
from app.models.audit import Approval, AuditLog
from app.models.user import User
from app.schemas.agent import AgentDecisionOut, ApprovalAction

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schemas
# ---------------------------------------------------------------------------

class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    decision_id: int
    title: str
    description: Optional[str] = None
    request_data: Optional[dict] = None
    status: str
    agent_name: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    decision: Optional[AgentDecisionOut] = None


async def _build_approval_out(approval: Approval, db: AsyncSession) -> ApprovalOut:
    decision_out: Optional[AgentDecisionOut] = None
    agent_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None

    if approval.decision_id:
        dec_result = await db.execute(
            select(AgentDecision)
            .options(selectinload(AgentDecision.agent))
            .where(AgentDecision.id == approval.decision_id)
        )
        decision = dec_result.scalar_one_or_none()
        if decision:
            decision_out = AgentDecisionOut.model_validate(decision)
            agent_name = decision.agent.name if decision.agent else None

    if approval.reviewed_by_user_id:
        user_result = await db.execute(select(User).where(User.id == approval.reviewed_by_user_id))
        reviewer = user_result.scalar_one_or_none()
        if reviewer:
            reviewed_by_name = reviewer.full_name

    return ApprovalOut(
        id=approval.id,
        decision_id=approval.decision_id,
        title=approval.title,
        description=approval.description,
        request_data=approval.request_data,
        status=approval.status,
        agent_name=agent_name,
        reviewed_by=reviewed_by_name,
        review_notes=approval.review_notes,
        created_at=approval.created_at,
        reviewed_at=approval.reviewed_at,
        decision=decision_out,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/stats", summary="Approval statistics")
async def approval_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict:
    pending_result = await db.execute(
        select(func.count(Approval.id)).where(Approval.status == "PENDING")
    )
    pending = pending_result.scalar_one()

    today = datetime.now(timezone.utc).date()

    approved_result = await db.execute(
        select(func.count(Approval.id)).where(
            and_(
                Approval.status == "APPROVED",
                func.date(Approval.reviewed_at) == today,
            )
        )
    )
    approved_today = approved_result.scalar_one()

    rejected_result = await db.execute(
        select(func.count(Approval.id)).where(
            and_(
                Approval.status == "REJECTED",
                func.date(Approval.reviewed_at) == today,
            )
        )
    )
    rejected_today = rejected_result.scalar_one()

    return {
        "pending": pending,
        "approved_today": approved_today,
        "rejected_today": rejected_today,
    }


@router.get("/", response_model=list[ApprovalOut], summary="List approvals")
async def list_approvals(
    approval_status: Optional[str] = Query("PENDING", alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[ApprovalOut]:
    query = select(Approval).order_by(Approval.created_at.desc())
    if approval_status:
        query = query.where(Approval.status == approval_status)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    approvals = result.scalars().all()

    return [await _build_approval_out(a, db) for a in approvals]


@router.get("/{approval_id}", response_model=ApprovalOut, summary="Get approval details")
async def get_approval(
    approval_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ApprovalOut:
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    return await _build_approval_out(approval, db)


@router.post("/{approval_id}/review", response_model=ApprovalOut, summary="Approve or reject a decision")
async def review_approval(
    approval_id: int,
    action: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApprovalOut:
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

    if approval.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval is already in status '{approval.status}'",
        )

    now = datetime.now(timezone.utc)
    new_status = action.action.upper()  # "APPROVED" or "REJECTED"

    if new_status not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be APPROVED or REJECTED")

    # Update approval record
    approval.status = new_status
    approval.reviewed_by_user_id = current_user.id
    approval.review_notes = action.notes
    approval.reviewed_at = now

    # Mirror status on the linked AgentDecision
    if approval.decision_id:
        dec_result = await db.execute(
            select(AgentDecision).where(AgentDecision.id == approval.decision_id)
        )
        decision = dec_result.scalar_one_or_none()
        if decision:
            decision.status = (
                DecisionStatus.APPROVED.value
                if new_status == "APPROVED"
                else DecisionStatus.REJECTED.value
            )
            decision.approved_by_user_id = current_user.id
            decision.approval_notes = action.notes
            decision.approved_at = now

    # Audit log
    audit = AuditLog(
        actor_type="USER",
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        action=f"APPROVAL_{new_status}",
        entity_type="Approval",
        entity_id=approval_id,
        details={
            "approval_id": approval_id,
            "decision_id": approval.decision_id,
            "notes": action.notes,
            "new_status": new_status,
        },
    )
    db.add(audit)

    await db.flush()
    return await _build_approval_out(approval, db)
