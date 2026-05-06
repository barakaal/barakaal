from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.agent import Agent
from app.models.department import Department
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schemas (Department not in shared schemas module)
# ---------------------------------------------------------------------------

class DepartmentBase(BaseModel):
    name: str
    code: str
    description: str = ""
    budget_monthly_usd: float = 0.0
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    budget_monthly_usd: Optional[float] = None
    is_active: Optional[bool] = None


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_count: int = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[DepartmentOut], summary="List all departments")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[DepartmentOut]:
    result = await db.execute(select(Department).order_by(Department.name))
    departments = result.scalars().all()

    # Count agents per department
    counts_result = await db.execute(
        select(Agent.department_id, func.count(Agent.id).label("cnt"))
        .group_by(Agent.department_id)
    )
    counts = {row.department_id: row.cnt for row in counts_result}

    output = []
    for dept in departments:
        data = DepartmentOut.model_validate(dept)
        data.agent_count = counts.get(dept.id, 0)
        output.append(data)
    return output


@router.post(
    "/",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create department (ADMIN+)",
)
async def create_department(
    dept_in: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> DepartmentOut:
    existing = await db.execute(
        select(Department).where(
            (Department.name == dept_in.name) | (Department.code == dept_in.code)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department with this name or code already exists",
        )

    dept = Department(**dept_in.model_dump())
    db.add(dept)
    await db.flush()
    await db.refresh(dept)

    out = DepartmentOut.model_validate(dept)
    out.agent_count = 0
    return out


@router.get("/{dept_id}", response_model=DepartmentOut, summary="Get department with agents")
async def get_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> DepartmentOut:
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    count_result = await db.execute(
        select(func.count(Agent.id)).where(Agent.department_id == dept_id)
    )
    agent_count = count_result.scalar_one()

    out = DepartmentOut.model_validate(dept)
    out.agent_count = agent_count
    return out


@router.put("/{dept_id}", response_model=DepartmentOut, summary="Update department")
async def update_department(
    dept_id: int,
    dept_in: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> DepartmentOut:
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    for field, value in dept_in.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)

    await db.flush()
    await db.refresh(dept)

    count_result = await db.execute(
        select(func.count(Agent.id)).where(Agent.department_id == dept_id)
    )
    agent_count = count_result.scalar_one()

    out = DepartmentOut.model_validate(dept)
    out.agent_count = agent_count
    return out
