"""
BaseAgent: abstract foundation for all AI agents in AI Dropship Company OS.

Every concrete agent inherits from this class. It provides:
  - Claude API interaction via anthropic.AsyncAnthropic
  - Conversation context / memory management
  - AgentTask lifecycle helpers (create / update)
  - AgentDecision + Approval workflow
  - AuditLog persistence
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.agent import (
    Agent,
    AgentDecision,
    AgentTask,
    DecisionStatus,
    RiskLevel,
    TaskPriority,
    TaskStatus,
)
from app.models.audit import Approval, AuditLog

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    # Subclasses should override this with a domain-specific prompt.
    SYSTEM_PROMPT: str = "Tu es un agent IA de la compagnie AI Dropship Company OS."

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    def __init__(self, agent_record: Agent, db: AsyncSession) -> None:
        self.agent_record = agent_record
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model: str = settings.AI_MODEL
        # Multi-turn context kept in memory for the lifetime of the agent
        # instance (one per request typically).
        self.conversation_history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Core LLM interaction
    # ------------------------------------------------------------------ #

    def _build_system_prompt(self) -> str:
        """Assemble a full system prompt from the class constant + agent DB record."""
        parts: list[str] = [self.SYSTEM_PROMPT.strip()]

        # Inject role description from DB record when available
        if self.agent_record.role_description:
            parts.append(
                f"\n## Rôle\n{self.agent_record.role_description}"
            )

        # Inject objectives
        if self.agent_record.objectives:
            objectives_text = "\n".join(
                f"- {obj}" for obj in self.agent_record.objectives
            )
            parts.append(f"\n## Objectifs\n{objectives_text}")

        # Inject permissions
        if self.agent_record.permissions:
            perms_text = "\n".join(
                f"- {p}" for p in self.agent_record.permissions
            )
            parts.append(f"\n## Permissions\n{perms_text}")

        # Inject memory summary if present
        if self.agent_record.memory_summary:
            parts.append(
                f"\n## Mémoire contextuelle (résumé)\n{self.agent_record.memory_summary}"
            )

        # Safety rules – always appended last
        parts.append(
            "\n## RÈGLES DE SÉCURITÉ ABSOLUES\n"
            "1. Toute dépense réelle > $0 doit passer par validation humaine.\n"
            "2. Tu ne peux jamais autoriser toi-même des achats ou remboursements.\n"
            "3. Toutes tes décisions doivent être documentées avec: raison, "
            "données utilisées, risque, recommandation.\n"
            "4. En cas de doute légal ou de conformité, refuser et escalader."
        )

        return "\n".join(parts)

    async def think(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """
        Call Claude API with the agent's full context.

        Parameters
        ----------
        prompt:
            The user-turn content for this call.
        system_prompt:
            If supplied, overrides the auto-built system prompt.
        tools:
            Optional list of tool definitions (Anthropic tool-use format).

        Returns
        -------
        str
            The text content of Claude's final response.
        """
        effective_system = system_prompt or self._build_system_prompt()

        # Maintain running conversation history
        self.conversation_history.append({"role": "user", "content": prompt})

        create_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "system": effective_system,
            "messages": self.conversation_history,
        }
        if tools:
            create_kwargs["tools"] = tools

        try:
            response = await self.client.messages.create(**create_kwargs)
        except anthropic.APIError as exc:
            logger.error(
                "Anthropic API error for agent %s: %s",
                self.agent_record.name,
                exc,
            )
            raise

        # Extract text from response, handling tool_use blocks gracefully
        text_parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            elif block.type == "tool_use":
                # Encode tool use as JSON so callers can detect it
                text_parts.append(
                    json.dumps({"tool_use": block.name, "input": block.input})
                )

        result_text = "\n".join(text_parts)

        # Add assistant response to history
        self.conversation_history.append(
            {"role": "assistant", "content": result_text}
        )

        return result_text

    # ------------------------------------------------------------------ #
    # Task helpers
    # ------------------------------------------------------------------ #

    async def create_task(
        self,
        title: str,
        description: str,
        input_data: dict[str, Any],
        priority: str = TaskPriority.MEDIUM.value,
    ) -> AgentTask:
        """Persist a new AgentTask record and return it."""
        task = AgentTask(
            agent_id=self.agent_record.id,
            title=title,
            description=description,
            status=TaskStatus.PENDING.value,
            priority=priority,
            input_data=input_data,
            created_at=_utcnow(),
        )
        self.db.add(task)
        await self.db.flush()  # get the generated id
        await self.db.refresh(task)
        logger.debug(
            "Created task %d (%s) for agent %s",
            task.id,
            title,
            self.agent_record.name,
        )
        return task

    async def update_task_status(
        self,
        task: AgentTask,
        status: str,
        output_data: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update an AgentTask's status, timestamps and output."""
        task.status = status
        if status == TaskStatus.RUNNING.value and task.started_at is None:
            task.started_at = _utcnow()
        if status in (
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
            TaskStatus.CANCELLED.value,
        ):
            task.completed_at = _utcnow()
        if output_data is not None:
            task.output_data = output_data
        if error is not None:
            task.error_message = error[:2000]  # column is varchar(2000)
        await self.db.flush()

    # ------------------------------------------------------------------ #
    # Decision + approval workflow
    # ------------------------------------------------------------------ #

    async def create_decision(
        self,
        task: Optional[AgentTask],
        decision_type: str,
        title: str,
        rationale: str,
        data_used: dict[str, Any],
        risk_level: str,
        recommendation: str,
        estimated_cost_usd: Optional[float] = None,
        estimated_revenue_usd: Optional[float] = None,
        requires_human_approval: bool = True,
    ) -> AgentDecision:
        """
        Create an AgentDecision (and an Approval record if human sign-off
        is required and `settings.HUMAN_APPROVAL_REQUIRED` is True).
        """
        decision = AgentDecision(
            agent_id=self.agent_record.id,
            task_id=task.id if task else None,
            decision_type=decision_type,
            title=title,
            rationale=rationale,
            data_used=data_used,
            risk_level=risk_level,
            recommendation=recommendation,
            estimated_cost_usd=estimated_cost_usd,
            estimated_revenue_usd=estimated_revenue_usd,
            requires_human_approval=requires_human_approval,
            status=DecisionStatus.PENDING_APPROVAL.value,
            created_at=_utcnow(),
        )
        self.db.add(decision)
        await self.db.flush()
        await self.db.refresh(decision)

        # Create approval record when human sign-off is required
        if requires_human_approval and settings.HUMAN_APPROVAL_REQUIRED:
            approval = Approval(
                decision_id=decision.id,
                title=f"Approbation requise: {title}",
                description=(
                    f"Type: {decision_type}\n"
                    f"Rationale: {rationale}\n"
                    f"Risque: {risk_level}\n"
                    f"Recommandation: {recommendation}"
                ),
                request_data={
                    "decision_id": decision.id,
                    "decision_type": decision_type,
                    "risk_level": risk_level,
                    "estimated_cost_usd": estimated_cost_usd,
                    "estimated_revenue_usd": estimated_revenue_usd,
                },
                status="PENDING",
                requested_by_agent_id=self.agent_record.id,
                created_at=_utcnow(),
            )
            self.db.add(approval)
            await self.db.flush()

        # Audit log
        await self.log_action(
            action="CREATE_DECISION",
            entity_type="agent_decision",
            entity_id=decision.id,
            description=(
                f"Agent {self.agent_record.name} a créé une décision: {title} "
                f"(type={decision_type}, risk={risk_level}, "
                f"approval_required={requires_human_approval})"
            ),
            new_data={
                "decision_type": decision_type,
                "risk_level": risk_level,
                "requires_human_approval": requires_human_approval,
            },
        )

        return decision

    # ------------------------------------------------------------------ #
    # Audit log
    # ------------------------------------------------------------------ #

    async def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        description: str,
        old_data: Optional[dict[str, Any]] = None,
        new_data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Persist an entry in audit_logs."""
        log_entry = AuditLog(
            actor_type="AGENT",
            actor_id=self.agent_record.id,
            actor_name=self.agent_record.name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_data=old_data,
            new_data=new_data,
            created_at=_utcnow(),
        )
        self.db.add(log_entry)
        await self.db.flush()

    # ------------------------------------------------------------------ #
    # Memory
    # ------------------------------------------------------------------ #

    async def update_memory(self, summary: str) -> None:
        """Persist a new memory summary on the agent DB record."""
        old_memory = self.agent_record.memory_summary
        self.agent_record.memory_summary = summary
        await self.db.flush()
        await self.log_action(
            action="UPDATE_MEMORY",
            entity_type="agent",
            entity_id=self.agent_record.id,
            description=f"Mémoire mise à jour pour {self.agent_record.name}",
            old_data={"memory_summary": old_memory},
            new_data={"memory_summary": summary},
        )

    # ------------------------------------------------------------------ #
    # Abstract interface
    # ------------------------------------------------------------------ #

    @abstractmethod
    async def execute(self, task_input: dict[str, Any]) -> dict[str, Any]:
        """Main execution entry-point. Must be implemented by every agent."""
        ...

    @abstractmethod
    async def generate_report(self) -> dict[str, Any]:
        """Return a structured status/activity report for this agent."""
        ...
