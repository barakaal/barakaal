from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.agent import AgentDecision, DecisionStatus
from app.models.audit import Approval
from app.models.campaign import Campaign
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schemas
# ---------------------------------------------------------------------------

class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    platform: Optional[str] = None
    budget_usd: float = 0.0
    target_audience: Optional[dict] = None
    ad_content: Optional[dict] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    platform: Optional[str] = None
    budget_usd: Optional[float] = None
    target_audience: Optional[dict] = None
    ad_content: Optional[dict] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class CampaignOut(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    requires_approval: bool = False
    approval_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[CampaignOut], summary="List campaigns")
async def list_campaigns(
    campaign_status: Optional[str] = Query(None, alias="status"),
    platform: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[CampaignOut]:
    query = select(Campaign)
    if campaign_status:
        query = query.where(Campaign.status == campaign_status)
    if platform:
        query = query.where(Campaign.platform == platform)
    query = query.order_by(Campaign.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return [CampaignOut.model_validate(c) for c in result.scalars().all()]


@router.post(
    "/",
    response_model=CampaignOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create campaign (DRAFT status; triggers approval if budget > 0)",
)
async def create_campaign(
    campaign_in: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CampaignOut:
    requires_approval = settings.HUMAN_APPROVAL_REQUIRED and campaign_in.budget_usd > 0

    campaign = Campaign(
        **campaign_in.model_dump(),
        status="DRAFT",
    )
    db.add(campaign)
    await db.flush()

    approval_id: Optional[int] = None
    if requires_approval:
        # Create a pending approval record
        decision = AgentDecision(
            agent_id=1,  # system agent placeholder
            decision_type="CAMPAIGN_LAUNCH",
            title=f"Campaign: {campaign_in.name}",
            rationale=f"Human approval required for campaign with budget ${campaign_in.budget_usd}",
            risk_level="MEDIUM",
            recommendation="Review and approve or reject this campaign",
            estimated_cost_usd=campaign_in.budget_usd,
            status=DecisionStatus.PENDING_APPROVAL.value,
            requires_human_approval=True,
            data_used={"campaign_id": campaign.id, "budget_usd": campaign_in.budget_usd},
        )
        db.add(decision)
        await db.flush()

        approval = Approval(
            decision_id=decision.id,
            title=f"Approve campaign: {campaign_in.name}",
            description=campaign_in.description or "",
            request_data={"campaign_id": campaign.id, "budget_usd": campaign_in.budget_usd},
            status="PENDING",
        )
        db.add(approval)
        await db.flush()
        approval_id = approval.id

    await db.refresh(campaign)
    out = CampaignOut.model_validate(campaign)
    out.requires_approval = requires_approval
    out.approval_id = approval_id
    return out


@router.get("/{campaign_id}", response_model=CampaignOut, summary="Get campaign by ID")
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> CampaignOut:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return CampaignOut.model_validate(campaign)


@router.put("/{campaign_id}", response_model=CampaignOut, summary="Update campaign")
async def update_campaign(
    campaign_id: int,
    campaign_in: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> CampaignOut:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign.status == "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit an active campaign. Deactivate it first.",
        )

    for field, value in campaign_in.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)

    await db.flush()
    await db.refresh(campaign)
    return CampaignOut.model_validate(campaign)


@router.post("/{campaign_id}/activate", response_model=CampaignOut, summary="Activate or submit campaign for approval")
async def activate_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CampaignOut:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign.status == "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign is already active")

    approval_id: Optional[int] = None
    requires_approval = settings.HUMAN_APPROVAL_REQUIRED

    if requires_approval:
        # Submit for human approval instead of direct activation
        campaign.status = "PENDING_APPROVAL"

        decision = AgentDecision(
            agent_id=1,
            decision_type="CAMPAIGN_ACTIVATE",
            title=f"Activate campaign: {campaign.name}",
            rationale="Human approval required before campaign launch",
            risk_level="MEDIUM",
            recommendation="Review campaign settings and approve activation",
            estimated_cost_usd=campaign.budget_usd,
            status=DecisionStatus.PENDING_APPROVAL.value,
            requires_human_approval=True,
            data_used={"campaign_id": campaign.id},
        )
        db.add(decision)
        await db.flush()

        approval = Approval(
            decision_id=decision.id,
            title=f"Activate campaign: {campaign.name}",
            description=campaign.description or "",
            request_data={"campaign_id": campaign.id, "budget_usd": campaign.budget_usd},
            status="PENDING",
        )
        db.add(approval)
        await db.flush()
        approval_id = approval.id
    else:
        campaign.status = "ACTIVE"

    await db.flush()
    await db.refresh(campaign)
    out = CampaignOut.model_validate(campaign)
    out.requires_approval = requires_approval
    out.approval_id = approval_id
    return out
