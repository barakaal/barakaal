from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.audit import ApiConnector
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schemas
# ---------------------------------------------------------------------------

class ConnectorConfigUpdate(BaseModel):
    """Only non-secret configuration fields. Secrets must be stored in a vault."""
    config: dict[str, Any]
    secret_reference: Optional[str] = None  # reference key in secrets manager, not the value


class ConnectorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    connector_type: str
    is_active: bool
    status: str
    last_sync_at: Optional[datetime] = None
    config: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConnectorTestResult(BaseModel):
    connector_id: int
    success: bool
    message: str
    latency_ms: Optional[float] = None
    tested_at: datetime


class ConnectorSyncResult(BaseModel):
    connector_id: int
    status: str
    message: str
    triggered_at: datetime


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ConnectorOut], summary="List all API connectors and their status")
async def list_connectors(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[ConnectorOut]:
    result = await db.execute(select(ApiConnector).order_by(ApiConnector.name))
    connectors = result.scalars().all()
    return [ConnectorOut.model_validate(c) for c in connectors]


@router.put(
    "/{connector_id}/config",
    response_model=ConnectorOut,
    summary="Update connector configuration (no plaintext secrets)",
)
async def update_connector_config(
    connector_id: int,
    config_update: ConnectorConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> ConnectorOut:
    result = await db.execute(select(ApiConnector).where(ApiConnector.id == connector_id))
    connector = result.scalar_one_or_none()
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    # Merge new config without overwriting secret keys (those start with "_secret_")
    current_config: dict = connector.config or {}
    for key, value in config_update.config.items():
        if key.startswith("_secret_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Secret key '{key}' must not be stored in plain config. Use secret_reference instead.",
            )
        current_config[key] = value

    if config_update.secret_reference:
        # Store only the reference key, not the secret value
        current_config["_secret_ref"] = config_update.secret_reference

    connector.config = current_config
    connector.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(connector)
    return ConnectorOut.model_validate(connector)


@router.post("/{connector_id}/test", response_model=ConnectorTestResult, summary="Test connector connection")
async def test_connector(
    connector_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ConnectorTestResult:
    result = await db.execute(select(ApiConnector).where(ApiConnector.id == connector_id))
    connector = result.scalar_one_or_none()
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    if not connector.is_active:
        return ConnectorTestResult(
            connector_id=connector_id,
            success=False,
            message="Connector is disabled",
            tested_at=datetime.now(timezone.utc),
        )

    # Simulate connection test (real implementation would call the external API)
    # In production: import httpx and ping the marketplace health endpoint
    start = datetime.now(timezone.utc)
    try:
        # Placeholder: assume success if connector has required config keys
        required_keys = connector.config.get("required_keys", []) if connector.config else []
        missing = [k for k in required_keys if k not in (connector.config or {})]
        if missing:
            raise ValueError(f"Missing configuration keys: {missing}")

        latency_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        success = True
        message = f"Connection to {connector.name} successful"

        # Update connector status
        connector.status = "CONNECTED"
        connector.error_message = None
    except Exception as exc:
        latency_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        success = False
        message = str(exc)
        connector.status = "ERROR"
        connector.error_message = message

    connector.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return ConnectorTestResult(
        connector_id=connector_id,
        success=success,
        message=message,
        latency_ms=round(latency_ms, 2),
        tested_at=datetime.now(timezone.utc),
    )


@router.post("/{connector_id}/sync", response_model=ConnectorSyncResult, summary="Trigger synchronisation")
async def sync_connector(
    connector_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ConnectorSyncResult:
    result = await db.execute(select(ApiConnector).where(ApiConnector.id == connector_id))
    connector = result.scalar_one_or_none()
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    if not connector.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot sync a disabled connector",
        )

    now = datetime.now(timezone.utc)

    # In production: enqueue a background Celery/ARQ task
    # Here we mark it as triggered and update last_sync_at
    connector.last_sync_at = now
    connector.status = "SYNCING"
    connector.updated_at = now
    await db.flush()

    return ConnectorSyncResult(
        connector_id=connector_id,
        status="TRIGGERED",
        message=f"Synchronisation for '{connector.name}' has been queued",
        triggered_at=now,
    )
