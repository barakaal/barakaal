from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.core.security import hash_password
from app.models.user import Role, User
from app.schemas.common import PaginatedResponse
from app.schemas.user import RoleOut, UserCreate, UserOut, UserUpdate

router = APIRouter()


@router.get("/roles/", response_model=list[RoleOut], summary="List all roles")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[RoleOut]:
    result = await db.execute(select(Role).order_by(Role.name))
    roles = result.scalars().all()
    return [RoleOut.model_validate(r) for r in roles]


@router.get("/", response_model=PaginatedResponse[UserOut], summary="List users with pagination")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> PaginatedResponse[UserOut]:
    offset = (page - 1) * page_size

    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()

    return PaginatedResponse(
        items=[UserOut.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> UserOut:
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    role_result = await db.execute(select(Role).where(Role.id == user_in.role_id))
    if role_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role {user_in.role_id} not found")

    new_user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role_id=user_in.role_id,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user, attribute_names=["role"])
    return UserOut.model_validate(new_user)


@router.get("/{user_id}", response_model=UserOut, summary="Get user by ID")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    # Users can view their own profile; admins can view any
    if current_user.id != user_id and (
        current_user.role is None or current_user.role.name not in ("ADMIN", "SUPER_ADMIN")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut, summary="Update user")
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    # Users can update their own profile; admins can update any
    if current_user.id != user_id and (
        current_user.role is None or current_user.role.name not in ("ADMIN", "SUPER_ADMIN")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user, attribute_names=["role"])
    return UserOut.model_validate(user)


@router.delete("/{user_id}", summary="Delete user (SUPER_ADMIN only)")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN")),
) -> dict:
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    return {"message": f"User {user_id} deleted successfully"}
