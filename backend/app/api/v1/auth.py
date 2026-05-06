from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.schemas.user import Token, UserCreate, UserOut

router = APIRouter()


@router.post("/login", response_model=Token, summary="Authenticate and get JWT token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    access_token = create_access_token(data={"user_id": user.id, "role": user.role.name})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    # Only SUPER_ADMIN can register new users
    if current_user.role is None or current_user.role.name not in ("SUPER_ADMIN", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create new users",
        )

    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Validate role exists
    role_result = await db.execute(select(Role).where(Role.id == user_in.role_id))
    role = role_result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {user_in.role_id} not found",
        )

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


@router.get("/me", response_model=UserOut, summary="Get current authenticated user")
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    return UserOut.model_validate(current_user)


@router.post("/logout", summary="Logout (client-side token invalidation)")
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    # JWT is stateless; logout is handled client-side by discarding the token.
    # Future enhancement: maintain a token blacklist in Redis.
    return {"message": "Successfully logged out"}
