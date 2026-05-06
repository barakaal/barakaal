from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.agent import Agent, AgentDecision, AgentTask, DecisionStatus, TaskStatus
from app.models.user import User
from app.schemas.agent import (
    AgentCreate,
    AgentDecisionOut,
    AgentOut,
    AgentTaskCreate,
    AgentTaskOut,
    AgentUpdate,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Tasks (collection routes — must be before /{id} to avoid route conflicts)
# ---------------------------------------------------------------------------

@router.get("/tasks/", response_model=list[AgentTaskOut], summary="List all agent tasks")
async def list_all_tasks(
    task_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[AgentTaskOut]:
    query = select(AgentTask).order_by(AgentTask.created_at.desc())
    if task_status:
        query = query.where(AgentTask.status == task_status)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return [AgentTaskOut.model_validate(t) for t in tasks]


@router.get("/decisions/", response_model=list[AgentDecisionOut], summary="List all agent decisions")
async def list_all_decisions(
    decision_status: Optional[str] = Query(None, alias="status"),
    risk_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[AgentDecisionOut]:
    query = select(AgentDecision).order_by(AgentDecision.created_at.desc())
    if decision_status:
        query = query.where(AgentDecision.status == decision_status)
    if risk_level:
        query = query.where(AgentDecision.risk_level == risk_level)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    decisions = result.scalars().all()
    return [AgentDecisionOut.model_validate(d) for d in decisions]


# ---------------------------------------------------------------------------
# Agents CRUD
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedResponse[AgentOut], summary="List agents with filters")
async def list_agents(
    department_id: Optional[int] = Query(None),
    agent_type: Optional[str] = Query(None),
    agent_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PaginatedResponse[AgentOut]:
    base_query = select(Agent)
    if department_id is not None:
        base_query = base_query.where(Agent.department_id == department_id)
    if agent_type:
        base_query = base_query.where(Agent.agent_type == agent_type)
    if agent_status:
        base_query = base_query.where(Agent.status == agent_status)

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.order_by(Agent.name).offset((page - 1) * page_size).limit(page_size)
    )
    agents = result.scalars().all()

    return PaginatedResponse(
        items=[AgentOut.model_validate(a) for a in agents],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=AgentOut, status_code=status.HTTP_201_CREATED, summary="Create agent (ADMIN+)")
async def create_agent(
    agent_in: AgentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> AgentOut:
    agent = Agent(**agent_in.model_dump())
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return AgentOut.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentOut, summary="Get agent by ID")
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> AgentOut:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return AgentOut.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentOut, summary="Update agent")
async def update_agent(
    agent_id: int,
    agent_in: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> AgentOut:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    for field, value in agent_in.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)

    await db.flush()
    await db.refresh(agent)
    return AgentOut.model_validate(agent)


@router.delete("/{agent_id}", summary="Delete agent")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> dict:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    await db.delete(agent)
    return {"message": f"Agent {agent_id} deleted successfully"}


# ---------------------------------------------------------------------------
# Agent-specific task / decision management
# ---------------------------------------------------------------------------

@router.post("/{agent_id}/run-task", response_model=AgentTaskOut, status_code=status.HTTP_201_CREATED, summary="Run a task on an agent")
async def run_agent_task(
    agent_id: int,
    task_in: AgentTaskCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> AgentTaskOut:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not agent.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent is not active")

    task = AgentTask(
        agent_id=agent_id,
        title=task_in.title,
        description=task_in.description,
        input_data=task_in.input_data or {},
        status=TaskStatus.PENDING.value,
        started_at=datetime.now(timezone.utc),
    )
    db.add(task)

    # Update agent status to RUNNING
    agent.status = "RUNNING"
    agent.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(task)
    return AgentTaskOut.model_validate(task)


@router.get("/{agent_id}/tasks", response_model=list[AgentTaskOut], summary="Get tasks for an agent")
async def get_agent_tasks(
    agent_id: int,
    task_status: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[AgentTaskOut]:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    query = select(AgentTask).where(AgentTask.agent_id == agent_id).order_by(AgentTask.created_at.desc())
    if task_status:
        query = query.where(AgentTask.status == task_status)

    tasks_result = await db.execute(query)
    return [AgentTaskOut.model_validate(t) for t in tasks_result.scalars().all()]


@router.get("/{agent_id}/decisions", response_model=list[AgentDecisionOut], summary="Get decisions for an agent")
async def get_agent_decisions(
    agent_id: int,
    decision_status: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[AgentDecisionOut]:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    query = (
        select(AgentDecision)
        .where(AgentDecision.agent_id == agent_id)
        .order_by(AgentDecision.created_at.desc())
    )
    if decision_status:
        query = query.where(AgentDecision.status == decision_status)

    decisions_result = await db.execute(query)
    return [AgentDecisionOut.model_validate(d) for d in decisions_result.scalars().all()]
