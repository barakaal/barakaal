from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.models.audit import AuditLog


async def log(
    db: AsyncSession,
    actor_type: str,
    actor_id: int,
    actor_name: str,
    action: str,
    entity_type: str,
    description: str,
    entity_id: int = None,
    old_data: dict = None,
    new_data: dict = None,
    ip_address: str = None,
) -> AuditLog:
    """
    Crée une entrée dans le journal d'audit.

    Paramètres:
      - actor_type: "USER" | "AGENT" | "SYSTEM"
      - actor_id: ID de l'utilisateur ou de l'agent
      - actor_name: Nom lisible de l'acteur
      - action: Code d'action (ex: "CREATE_PRODUCT", "APPROVE_DECISION")
      - entity_type: Type d'entité concernée (ex: "product", "agent_decision")
      - description: Description lisible de l'action
      - entity_id: ID de l'entité concernée (optionnel)
      - old_data: Données avant modification (optionnel)
      - new_data: Données après modification (optionnel)
      - ip_address: Adresse IP de l'acteur (optionnel)
    """
    log_entry = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        actor_name=actor_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_data=old_data,
        new_data=new_data,
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry


async def log_user_action(
    db: AsyncSession,
    user_id: int,
    user_name: str,
    action: str,
    entity_type: str,
    description: str,
    entity_id: int = None,
    old_data: dict = None,
    new_data: dict = None,
    ip_address: str = None,
) -> AuditLog:
    """Raccourci pour logger une action utilisateur."""
    return await log(
        db=db,
        actor_type="USER",
        actor_id=user_id,
        actor_name=user_name,
        action=action,
        entity_type=entity_type,
        description=description,
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        ip_address=ip_address,
    )


async def log_agent_action(
    db: AsyncSession,
    agent_id: int,
    agent_name: str,
    action: str,
    entity_type: str,
    description: str,
    entity_id: int = None,
    old_data: dict = None,
    new_data: dict = None,
) -> AuditLog:
    """Raccourci pour logger une action agent IA."""
    return await log(
        db=db,
        actor_type="AGENT",
        actor_id=agent_id,
        actor_name=agent_name,
        action=action,
        entity_type=entity_type,
        description=description,
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
    )


async def log_system_action(
    db: AsyncSession,
    action: str,
    entity_type: str,
    description: str,
    entity_id: int = None,
    new_data: dict = None,
) -> AuditLog:
    """Raccourci pour logger une action système automatique."""
    return await log(
        db=db,
        actor_type="SYSTEM",
        actor_id=0,
        actor_name="SYSTEM",
        action=action,
        entity_type=entity_type,
        description=description,
        entity_id=entity_id,
        new_data=new_data,
    )


async def get_audit_logs(
    db: AsyncSession,
    entity_type: str = None,
    entity_id: int = None,
    actor_type: str = None,
    actor_id: int = None,
    action: str = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[AuditLog], int]:
    """
    Récupère les entrées d'audit avec filtres optionnels.
    Retourne (logs, total).
    """
    stmt = select(AuditLog)

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_type:
        stmt = stmt.where(AuditLog.actor_type == actor_type)
    if actor_id is not None:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    offset = (page - 1) * size
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(stmt)
    logs = list(result.scalars().all())

    return logs, total
