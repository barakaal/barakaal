"""
AgentFactory: creates agent instances from DB records.

Usage:
    agent = await create_agent(agent_record, db)
    result = await agent.execute({"action": "weekly_review", "data": {...}})

    # Or by name (auto-creates DB record if missing):
    agent = await create_agent_by_name(db, "ceo")

The factory maps agent_record.name (normalized) or a type key to the correct class.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.agents.ceo_agent import CEOAgent
from app.agents.employees.fraud_detector import FraudDetectorAgent
from app.agents.employees.product_writer import ProductWriterAgent
from app.agents.employees.trend_analysts import (
    AliExpressTrendAnalyst,
    AmazonTrendAnalyst,
    EbayTrendAnalyst,
    GoogleTrendAnalyst,
    TikTokTrendAnalyst,
)
from app.agents.managers.compliance_manager import ComplianceManagerAgent
from app.agents.managers.customer_support_manager import CustomerSupportManagerAgent
from app.agents.managers.finance_manager import FinanceManagerAgent
from app.agents.managers.marketing_manager import MarketingManagerAgent
from app.agents.managers.order_manager import OrderManagerAgent
from app.agents.managers.product_research_manager import ProductResearchManagerAgent
from app.agents.managers.sourcing_manager import SourcingManagerAgent
from app.models.agent import Agent, AgentStatus, AgentType

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry: maps string keys → agent classes
# Keys are lowercase, underscore-separated identifiers.
# ---------------------------------------------------------------------------

AGENT_CLASS_MAP: dict[str, Type[BaseAgent]] = {
    # CEO
    "ceo": CEOAgent,
    "ceo_agent": CEOAgent,
    # Managers
    "product_research_manager": ProductResearchManagerAgent,
    "sourcing_manager": SourcingManagerAgent,
    "marketing_manager": MarketingManagerAgent,
    "order_manager": OrderManagerAgent,
    "finance_manager": FinanceManagerAgent,
    "customer_support_manager": CustomerSupportManagerAgent,
    "compliance_manager": ComplianceManagerAgent,
    # Employee — trend analysts
    "amazon_trend_analyst": AmazonTrendAnalyst,
    "aliexpress_trend_analyst": AliExpressTrendAnalyst,
    "tiktok_trend_analyst": TikTokTrendAnalyst,
    "google_trend_analyst": GoogleTrendAnalyst,
    "ebay_trend_analyst": EbayTrendAnalyst,
    # Employee — specialists
    "product_writer": ProductWriterAgent,
    "fraud_detector": FraudDetectorAgent,
}

# Default DB record configurations for auto-created agents
_DEFAULT_AGENT_CONFIGS: dict[str, dict] = {
    "ceo": {
        "name": "CEO",
        "agent_type": AgentType.CEO.value,
        "role_description": "CEO IA orchestrateur de l'entreprise de dropshipping.",
        "objectives": [
            "Maximiser la croissance durable de l'entreprise",
            "Coordonner tous les managers",
            "Valider les décisions stratégiques",
        ],
        "permissions": ["read:all", "write:decisions", "approve:decisions"],
        "tools": ["weekly_review", "strategic_decision", "department_report", "growth_planning"],
    },
    "product_research_manager": {
        "name": "ProductResearchManager",
        "agent_type": AgentType.MANAGER.value,
        "role_description": "Manager IA responsable de la recherche de produits gagnants.",
        "objectives": [
            "Identifier 5-10 produits gagnants par semaine",
            "Analyser les tendances multi-plateformes",
            "Évaluer la viabilité commerciale de chaque produit",
        ],
        "permissions": ["read:trends", "write:products", "write:decisions"],
        "tools": ["evaluate_products", "trend_analysis", "catalog_update", "competitive_analysis"],
    },
    "sourcing_manager": {
        "name": "SourcingManager",
        "agent_type": AgentType.MANAGER.value,
        "role_description": "Manager IA responsable du sourcing fournisseurs.",
        "objectives": [
            "Trouver les meilleurs fournisseurs pour chaque produit",
            "Négocier les prix et délais de livraison",
            "Évaluer la fiabilité des fournisseurs",
        ],
        "permissions": ["read:products", "read:suppliers", "write:decisions"],
        "tools": ["evaluate_supplier", "compare_suppliers", "monitor_performance", "recommend_order"],
    },
    "marketing_manager": {
        "name": "MarketingManager",
        "agent_type": AgentType.MANAGER.value,
        "role_description": "Manager IA responsable des campagnes marketing.",
        "objectives": [
            "Optimiser le ROAS des campagnes publicitaires",
            "Gérer le budget marketing efficacement",
            "Maximiser les conversions et la croissance",
        ],
        "permissions": ["read:analytics", "write:campaigns", "write:decisions"],
        "tools": ["analyze_campaigns", "optimize_budget", "content_strategy", "campaign_proposal"],
    },
    "order_manager": {
        "name": "OrderManager",
        "agent_type": AgentType.MANAGER.value,
        "role_description": "Manager IA responsable du traitement des commandes.",
        "objectives": [
            "Maintenir un taux de livraison à temps > 95%",
            "Réduire les taux de retour",
            "Résoudre rapidement les problèmes de fulfillment",
        ],
        "permissions": ["read:orders", "write:orders", "write:decisions"],
        "tools": ["monitor_orders", "handle_issue", "process_returns", "fulfillment_optimization"],
    },
    "finance_manager": {
        "name": "FinanceManager",
        "agent_type": AgentType.MANAGER.value,
        "role_description": "Manager IA responsable de la gestion financière.",
        "objectives": [
            "Maintenir une marge brute > 30%",
            "Surveiller les flux de trésorerie",
            "Produire des rapports financiers hebdomadaires",
        ],
        "permissions": ["read:finances", "write:reports", "write:decisions"],
        "tools": ["financial_report", "budget_analysis", "cash_flow_forecast", "profitability_analysis"],
    },
    "customer_support_manager": {
        "name": "CustomerSupportManager",
        "agent_type": AgentType.MANAGER.value,
        "role_description": "Manager IA responsable du support client.",
        "objectives": [
            "Maintenir un CSAT > 90%",
            "Réduire le temps de réponse moyen",
            "Identifier et résoudre les problèmes systémiques",
        ],
        "permissions": ["read:tickets", "write:resolutions", "write:decisions"],
        "tools": ["analyze_tickets", "escalation_policy", "csat_analysis", "resolve_complaint"],
    },
    "compliance_manager": {
        "name": "ComplianceManager",
        "agent_type": AgentType.MANAGER.value,
        "role_description": "Manager IA responsable de la conformité légale.",
        "objectives": [
            "Assurer la conformité légale de tous les produits",
            "Prévenir les risques de suspension de comptes marketplace",
            "Maintenir la conformité RGPD/CCPA",
        ],
        "permissions": ["read:all", "write:compliance_reports", "block:products", "write:decisions"],
        "tools": ["compliance_check", "product_review", "platform_policy_audit", "data_privacy_check"],
    },
    "amazon_trend_analyst": {
        "name": "AmazonTrendAnalyst",
        "agent_type": AgentType.EMPLOYEE.value,
        "role_description": "Analyste tendances spécialisé sur Amazon.",
        "objectives": ["Identifier les produits trending sur Amazon", "Analyser les Best Sellers"],
        "permissions": ["read:trends"],
        "tools": ["analyze_trends"],
    },
    "aliexpress_trend_analyst": {
        "name": "AliExpressTrendAnalyst",
        "agent_type": AgentType.EMPLOYEE.value,
        "role_description": "Analyste tendances spécialisé sur AliExpress.",
        "objectives": ["Identifier les produits dropshipping sur AliExpress"],
        "permissions": ["read:trends"],
        "tools": ["analyze_trends"],
    },
    "tiktok_trend_analyst": {
        "name": "TikTokTrendAnalyst",
        "agent_type": AgentType.EMPLOYEE.value,
        "role_description": "Analyste tendances spécialisé sur TikTok.",
        "objectives": ["Identifier les produits viraux sur TikTok"],
        "permissions": ["read:trends"],
        "tools": ["analyze_trends"],
    },
    "google_trend_analyst": {
        "name": "GoogleTrendAnalyst",
        "agent_type": AgentType.EMPLOYEE.value,
        "role_description": "Analyste tendances spécialisé sur Google.",
        "objectives": ["Analyser les tendances de recherche Google", "Identifier les opportunités SEO"],
        "permissions": ["read:trends"],
        "tools": ["analyze_trends"],
    },
    "ebay_trend_analyst": {
        "name": "EbayTrendAnalyst",
        "agent_type": AgentType.EMPLOYEE.value,
        "role_description": "Analyste tendances spécialisé sur eBay.",
        "objectives": ["Identifier les produits trending sur eBay"],
        "permissions": ["read:trends"],
        "tools": ["analyze_trends"],
    },
    "product_writer": {
        "name": "ProductWriter",
        "agent_type": AgentType.EMPLOYEE.value,
        "role_description": "Rédacteur de fiches produits SEO-optimisées.",
        "objectives": ["Créer des fiches produits optimisées", "Améliorer les taux de conversion"],
        "permissions": ["read:products", "write:listings"],
        "tools": ["write_listing", "optimize_listing", "generate_variants", "write_ad_copy"],
    },
    "fraud_detector": {
        "name": "FraudDetector",
        "agent_type": AgentType.EMPLOYEE.value,
        "role_description": "Spécialiste détection de fraude et sécurité des paiements.",
        "objectives": ["Détecter les commandes frauduleuses", "Maintenir le taux de chargeback < 1%"],
        "permissions": ["read:orders", "read:payments", "write:decisions", "block:orders"],
        "tools": ["analyze_order", "batch_screening", "chargeback_analysis", "customer_risk_profile"],
    },
}


def _normalize_key(raw: str) -> str:
    """Normalize an agent name/key to canonical lowercase_underscore form."""
    return raw.strip().lower().replace(" ", "_").replace("-", "_")


def get_agent_class(agent_type_key: str) -> Optional[Type[BaseAgent]]:
    """
    Look up an agent class by its type key.

    Parameters
    ----------
    agent_type_key:
        A string key such as "ceo", "marketing_manager", "fraud_detector".
        Case-insensitive, spaces and dashes normalized to underscores.

    Returns
    -------
    type[BaseAgent] | None
        The corresponding agent class, or None if not found.
    """
    normalized = _normalize_key(agent_type_key)
    cls = AGENT_CLASS_MAP.get(normalized)
    if cls is None:
        logger.warning("AgentFactory: unknown agent type key '%s'", agent_type_key)
    return cls


async def get_or_create_agent_record(db: AsyncSession, agent_key: str) -> Agent:
    """
    Retrieve an Agent DB record by normalized key, or create a default one.

    Parameters
    ----------
    db:
        The async SQLAlchemy session.
    agent_key:
        The normalized agent key (e.g. "ceo", "marketing_manager").
    """
    normalized = _normalize_key(agent_key)
    config = _DEFAULT_AGENT_CONFIGS.get(normalized, {})
    display_name = config.get("name", agent_key)

    result = await db.execute(select(Agent).where(Agent.name == display_name))
    agent_record = result.scalar_one_or_none()

    if agent_record is None:
        agent_record = Agent(
            name=display_name,
            agent_type=config.get("agent_type", AgentType.EMPLOYEE.value),
            role_description=config.get("role_description", f"{display_name} agent"),
            objectives=config.get("objectives", []),
            permissions=config.get("permissions", []),
            tools=config.get("tools", []),
            status=AgentStatus.IDLE.value,
            is_active=True,
            config={},
        )
        db.add(agent_record)
        await db.flush()
        await db.refresh(agent_record)
        logger.info(
            "AgentFactory: created default agent record '%s' (id=%d)",
            display_name,
            agent_record.id,
        )

    return agent_record


async def create_agent(
    agent_record: Agent,
    db: AsyncSession,
    *,
    agent_type_key: Optional[str] = None,
) -> BaseAgent:
    """
    Instantiate the correct agent class for the given DB record.

    Resolution order:
      1. ``agent_type_key`` argument (explicit override)
      2. ``agent_record.name`` normalized
      3. ``agent_record.agent_type`` (fallback)

    Parameters
    ----------
    agent_record:
        The Agent ORM record from the database.
    db:
        The async SQLAlchemy session.
    agent_type_key:
        Optional explicit key to look up in AGENT_CLASS_MAP.

    Returns
    -------
    BaseAgent
        A fully initialized agent instance ready to call ``.execute()``.

    Raises
    ------
    ValueError
        If no matching agent class can be found.
    """
    # 1. Explicit override
    if agent_type_key:
        cls = get_agent_class(agent_type_key)
        if cls:
            logger.debug(
                "AgentFactory: creating %s for agent '%s' via explicit key '%s'",
                cls.__name__,
                agent_record.name,
                agent_type_key,
            )
            return cls(agent_record, db)

    # 2. Attempt by normalized name
    cls = get_agent_class(agent_record.name)
    if cls:
        logger.debug(
            "AgentFactory: creating %s for agent '%s' via name lookup",
            cls.__name__,
            agent_record.name,
        )
        return cls(agent_record, db)

    # 3. Fallback by agent_type field
    type_fallback_map: dict[str, Type[BaseAgent]] = {
        "CEO": CEOAgent,
        "MANAGER": ProductResearchManagerAgent,
        "EMPLOYEE": ProductWriterAgent,
    }
    fallback_cls = type_fallback_map.get(agent_record.agent_type.upper())
    if fallback_cls:
        logger.warning(
            "AgentFactory: no exact match for '%s' — falling back to %s (agent_type=%s)",
            agent_record.name,
            fallback_cls.__name__,
            agent_record.agent_type,
        )
        return fallback_cls(agent_record, db)

    raise ValueError(
        f"AgentFactory: cannot resolve agent class for name='{agent_record.name}' "
        f"agent_type='{agent_record.agent_type}'. "
        f"Available keys: {sorted(AGENT_CLASS_MAP.keys())}"
    )


async def create_agent_by_name(db: AsyncSession, agent_key: str) -> BaseAgent:
    """
    Convenience function: look up or auto-create the DB record, then instantiate.

    Parameters
    ----------
    db:
        The async SQLAlchemy session.
    agent_key:
        A key from AGENT_CLASS_MAP (e.g. "ceo", "fraud_detector").

    Returns
    -------
    BaseAgent
        A fully initialized agent instance.

    Raises
    ------
    ValueError
        If ``agent_key`` is not in AGENT_CLASS_MAP.
    """
    normalized = _normalize_key(agent_key)
    cls = AGENT_CLASS_MAP.get(normalized)
    if cls is None:
        raise ValueError(
            f"AgentFactory: unknown agent key '{agent_key}'. "
            f"Available: {sorted(AGENT_CLASS_MAP.keys())}"
        )

    agent_record = await get_or_create_agent_record(db, normalized)
    return cls(agent_record, db)


# Convenience shortcuts for the most commonly used agents
async def create_ceo_agent(db: AsyncSession) -> CEOAgent:
    """Shortcut to create the CEO agent."""
    record = await get_or_create_agent_record(db, "ceo")
    return CEOAgent(agent_record=record, db=db)


def list_available_agents() -> list[str]:
    """Return a sorted list of all registered agent type keys."""
    return sorted(AGENT_CLASS_MAP.keys())
