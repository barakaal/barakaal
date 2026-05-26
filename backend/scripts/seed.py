"""
Script de seed pour initialiser la base de données avec des données de démonstration.
Usage: python scripts/seed.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import SessionLocal as AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.department import Department
from app.models.agent import Agent, AgentType, AgentStatus
from app.models.product import Product, ProductStatus
from app.models.supplier import Supplier
from app.models.audit import ApiConnector, Setting
from datetime import datetime


async def seed_roles(db: AsyncSession):
    roles = [
        Role(name="SUPER_ADMIN", permissions=["*"]),
        Role(name="ADMIN", permissions=["read:*", "write:*", "approve:*"]),
        Role(name="OPERATOR", permissions=["read:*", "write:products", "write:orders"]),
        Role(name="VIEWER", permissions=["read:*"]),
    ]
    for r in roles:
        db.add(r)
    await db.commit()
    print("✓ Roles created")
    return roles


async def seed_admin_user(db: AsyncSession):
    from sqlalchemy import select
    result = await db.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
    role = result.scalar_one()

    admin = User(
        email="admin@dropship-os.com",
        password_hash=hash_password("Admin123!"),
        full_name="Super Admin",
        role_id=role.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(admin)
    await db.commit()
    print("✓ Admin user created: admin@dropship-os.com / Admin123!")


async def seed_departments(db: AsyncSession):
    departments = [
        Department(name="Recherche Produits", code="RESEARCH", description="Identification et analyse des produits tendances", budget_monthly_usd=500),
        Department(name="Sourcing Fournisseurs", code="SOURCING", description="Recherche et évaluation des fournisseurs", budget_monthly_usd=300),
        Department(name="Analyse de Marché", code="MARKET_ANALYSIS", description="Analyse des tendances et de la concurrence", budget_monthly_usd=400),
        Department(name="Pricing & Marges", code="PRICING", description="Optimisation des prix et des marges", budget_monthly_usd=200),
        Department(name="Marketing", code="MARKETING", description="Campagnes publicitaires et acquisition clients", budget_monthly_usd=2000),
        Department(name="Boutique en ligne", code="STORE", description="Gestion de la boutique et des fiches produits", budget_monthly_usd=300),
        Department(name="Gestion des Commandes", code="ORDERS", description="Traitement et suivi des commandes", budget_monthly_usd=200),
        Department(name="Service Client", code="CUSTOMER_SUPPORT", description="Support et satisfaction client", budget_monthly_usd=300),
        Department(name="Finance & Comptabilité", code="FINANCE", description="Suivi financier et rapports", budget_monthly_usd=200),
        Department(name="Légal & Conformité", code="LEGAL", description="Conformité légale et réglementaire", budget_monthly_usd=300),
        Department(name="Data & Reporting", code="DATA", description="Analyses de données et tableaux de bord", budget_monthly_usd=200),
        Department(name="Technique / DevOps", code="TECH", description="Infrastructure et développement", budget_monthly_usd=500),
    ]
    for d in departments:
        db.add(d)
    await db.commit()
    print(f"✓ {len(departments)} departments created")


async def seed_agents(db: AsyncSession):
    from sqlalchemy import select

    depts = {d.code: d.id for d in (await db.execute(select(Department))).scalars().all()}

    agents = [
        Agent(name="CEO Alpha", agent_type=AgentType.CEO, role_description="Directeur Général IA supervisant toute la compagnie",
              objectives=["Maximiser la rentabilité", "Identifier les produits gagnants", "Assurer la conformité"],
              permissions=["read:*", "decide:strategic", "delegate:*"],
              tools=["weekly_review", "strategic_decision", "department_reporting"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "CEO"}),

        Agent(name="Chef Recherche Produits", agent_type=AgentType.MANAGER, department_id=depts.get("RESEARCH"),
              role_description="Directeur de la recherche produits, supervise les analystes tendances",
              objectives=["Trouver 10 produits candidats/semaine", "Score moyen > 70", "Détection précoce tendances"],
              permissions=["read:trends", "write:products", "delegate:employees"],
              tools=["analyze_trends", "product_evaluation", "weekly_research"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "PRODUCT_RESEARCH_MANAGER"}),

        Agent(name="Chef Sourcing", agent_type=AgentType.MANAGER, department_id=depts.get("SOURCING"),
              role_description="Directeur sourcing fournisseurs",
              objectives=["Identifier les meilleurs fournisseurs", "Négocier les meilleures conditions", "Calculer les marges"],
              permissions=["read:suppliers", "write:supplier_offers", "propose:sourcing"],
              tools=["compare_suppliers", "evaluate_supplier", "calculate_margins"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "SOURCING_MANAGER"}),

        Agent(name="Chef Marketing", agent_type=AgentType.MANAGER, department_id=depts.get("MARKETING"),
              role_description="Directeur marketing digital",
              objectives=["ROAS > 3x", "Créer des campagnes performantes", "Optimiser l'acquisition"],
              permissions=["read:campaigns", "propose:campaigns", "write:content"],
              tools=["create_campaign_strategy", "write_product_description", "create_ad_copy"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "MARKETING_MANAGER"}),

        Agent(name="Chef Commandes", agent_type=AgentType.MANAGER, department_id=depts.get("ORDERS"),
              role_description="Directeur gestion des commandes",
              objectives=["Traitement < 24h", "Taux satisfaction > 95%", "Fraude < 0.5%"],
              permissions=["read:orders", "update:order_status", "flag:fraud"],
              tools=["process_order", "check_fraud", "handle_issue"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "ORDER_MANAGER"}),

        Agent(name="Directeur Financier", agent_type=AgentType.MANAGER, department_id=depts.get("FINANCE"),
              role_description="Directeur financier IA",
              objectives=["Marge nette > 20%", "Rapports hebdomadaires", "Optimisation coûts"],
              permissions=["read:finance", "generate:reports", "analyze:profitability"],
              tools=["generate_report", "analyze_product_profitability", "budget_forecast"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "FINANCE_MANAGER"}),

        Agent(name="Chef Service Client", agent_type=AgentType.MANAGER, department_id=depts.get("CUSTOMER_SUPPORT"),
              role_description="Directeur service client",
              objectives=["Temps réponse < 2h", "Satisfaction > 4.5/5", "Résolution 1er contact > 80%"],
              permissions=["read:orders", "read:customers", "propose:refunds"],
              tools=["handle_inquiry", "draft_response", "handle_refund_request"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "CUSTOMER_SUPPORT_MANAGER"}),

        Agent(name="Directeur Conformité", agent_type=AgentType.MANAGER, department_id=depts.get("LEGAL"),
              role_description="Directeur légal et conformité",
              objectives=["0 violation légale", "Vérification conformité produits", "Protection données clients"],
              permissions=["read:*", "block:products", "require:compliance_review"],
              tools=["check_product", "check_supplier", "legal_review"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "COMPLIANCE_MANAGER"}),

        # Employés
        Agent(name="Analyste Amazon", agent_type=AgentType.EMPLOYEE, department_id=depts.get("RESEARCH"),
              role_description="Analyste tendances Amazon",
              objectives=["Identifier bestsellers", "Détecter produits montants"],
              permissions=["read:amazon_data"], tools=["amazon_trends"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "AMAZON_TREND_ANALYST"}),

        Agent(name="Analyste AliExpress", agent_type=AgentType.EMPLOYEE, department_id=depts.get("RESEARCH"),
              role_description="Analyste tendances AliExpress et sourcing",
              objectives=["Prix fournisseurs compétitifs", "Délais livraison optimaux"],
              permissions=["read:aliexpress_data"], tools=["aliexpress_trends"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "ALIEXPRESS_TREND_ANALYST"}),

        Agent(name="Analyste TikTok", agent_type=AgentType.EMPLOYEE, department_id=depts.get("MARKET_ANALYSIS"),
              role_description="Analyste tendances TikTok viral",
              objectives=["Détecter produits viraux", "Analyser engagement"],
              permissions=["read:tiktok_data"], tools=["tiktok_trends"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "TIKTOK_TREND_ANALYST"}),

        Agent(name="Analyste Google Trends", agent_type=AgentType.EMPLOYEE, department_id=depts.get("MARKET_ANALYSIS"),
              role_description="Analyste Google Trends et SEO",
              objectives=["Volume recherche", "Saisonnalité", "Keywords"],
              permissions=["read:google_data"], tools=["google_trends"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "GOOGLE_TREND_ANALYST"}),

        Agent(name="Rédacteur Fiches Produits", agent_type=AgentType.EMPLOYEE, department_id=depts.get("STORE"),
              role_description="Rédacteur SEO fiches produits",
              objectives=["Fiches optimisées SEO", "Taux conversion élevé"],
              permissions=["write:product_content"], tools=["write_product_description"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "PRODUCT_WRITER"}),

        Agent(name="Détecteur de Fraude", agent_type=AgentType.EMPLOYEE, department_id=depts.get("ORDERS"),
              role_description="Analyste fraude commandes",
              objectives=["Fraude < 0.5%", "Faux positifs < 2%"],
              permissions=["read:orders", "flag:fraud"], tools=["fraud_detection"],
              status=AgentStatus.IDLE, is_active=True, config={"class_name": "FRAUD_DETECTOR"}),
    ]

    for a in agents:
        a.created_at = datetime.utcnow()
        a.updated_at = datetime.utcnow()
        db.add(a)
    await db.commit()
    print(f"✓ {len(agents)} agents created")


async def seed_products(db: AsyncSession):
    products = [
        Product(name="Lampe LED Tactile Portable", description="Lampe de bureau rechargeable avec contrôle tactile et 3 niveaux de luminosité",
                category="Électronique", tags=["led", "lampe", "bureau", "rechargeable"],
                source_platform="ALIEXPRESS", score=82.5, status=ProductStatus.ACTIVE,
                cost_price_usd=8.50, selling_price_usd=29.99, gross_margin_pct=71.6,
                images=["https://picsum.photos/400/400?random=1"]),
        Product(name="Organisateur de Bureau Bambou", description="Organisateur multifonction en bambou naturel pour ranger stylos, cahiers et accessoires",
                category="Maison & Bureau", tags=["bambou", "organisateur", "bureau", "écologique"],
                source_platform="AMAZON", score=74.3, status=ProductStatus.APPROVED,
                cost_price_usd=12.00, selling_price_usd=39.99, gross_margin_pct=70.0,
                images=["https://picsum.photos/400/400?random=2"]),
        Product(name="Épurateur d'Air Mini USB", description="Épurateur d'air portable avec filtre HEPA et ioniseur, idéal pour bureau et voiture",
                category="Santé & Maison", tags=["air", "purificateur", "hepa", "usb"],
                source_platform="ALIEXPRESS", score=68.9, status=ProductStatus.UNDER_REVIEW,
                cost_price_usd=15.00, selling_price_usd=44.99, gross_margin_pct=66.7,
                images=["https://picsum.photos/400/400?random=3"]),
        Product(name="Masque LED Anti-Âge", description="Masque facial thérapie lumière rouge et bleue pour traitement acné et anti-âge",
                category="Beauté", tags=["masque", "led", "beauté", "anti-age"],
                source_platform="TIKTOK", score=88.2, status=ProductStatus.ACTIVE,
                cost_price_usd=18.00, selling_price_usd=59.99, gross_margin_pct=70.0,
                images=["https://picsum.photos/400/400?random=4"]),
        Product(name="Gourde Filtrante Outdoor", description="Gourde avec filtre intégré éliminant 99.9% des bactéries, idéale randonnée et camping",
                category="Sport & Outdoor", tags=["gourde", "filtre", "outdoor", "randonnée"],
                source_platform="EBAY", score=61.5, status=ProductStatus.CANDIDATE,
                cost_price_usd=9.00, selling_price_usd=27.99, gross_margin_pct=67.8,
                images=["https://picsum.photos/400/400?random=5"]),
    ]
    for p in products:
        p.created_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        db.add(p)
    await db.commit()
    print(f"✓ {len(products)} sample products created")


async def seed_suppliers(db: AsyncSession):
    suppliers = [
        Supplier(name="ShenZhen Electronics Co.", platform="ALIEXPRESS", country="CN",
                 rating=4.8, response_time_hours=12, min_order_qty=1,
                 payment_terms="Net 0", contact_info={"email": "contact@shenzhen-elec.com"},
                 is_verified=True, is_active=True),
        Supplier(name="EcoHome Supply", platform="ALIBABA", country="CN",
                 rating=4.6, response_time_hours=24, min_order_qty=5,
                 payment_terms="Net 30", contact_info={"email": "sales@ecohome.cn"},
                 is_verified=True, is_active=True),
        Supplier(name="BeautyTech Manufacturing", platform="ALIEXPRESS", country="CN",
                 rating=4.9, response_time_hours=8, min_order_qty=1,
                 payment_terms="Net 0", contact_info={"email": "beauty@techmanuf.cn"},
                 is_verified=True, is_active=True),
    ]
    for s in suppliers:
        s.created_at = datetime.utcnow()
        db.add(s)
    await db.commit()
    print(f"✓ {len(suppliers)} suppliers created")


async def seed_connectors(db: AsyncSession):
    connectors = [
        ApiConnector(name="Amazon PA-API", platform="AMAZON", config={"mode": "mock", "region": "us-east-1"}, is_active=True),
        ApiConnector(name="AliExpress DS API", platform="ALIEXPRESS", config={"mode": "mock"}, is_active=True),
        ApiConnector(name="eBay Browse API", platform="EBAY", config={"mode": "mock"}, is_active=True),
        ApiConnector(name="Google Trends", platform="GOOGLE_TRENDS", config={"mode": "mock", "geo": "US"}, is_active=True),
        ApiConnector(name="TikTok for Business", platform="TIKTOK", config={"mode": "mock"}, is_active=True),
        ApiConnector(name="CSV Import", platform="CSV_IMPORT", config={"mode": "live"}, is_active=True),
    ]
    for c in connectors:
        c.created_at = datetime.utcnow()
        db.add(c)
    await db.commit()
    print(f"✓ {len(connectors)} API connectors configured")


async def seed_settings(db: AsyncSession):
    settings_data = [
        Setting(key="weekly_workflow_enabled", value=True, category="scheduler", description="Active le workflow hebdomadaire automatique"),
        Setting(key="human_approval_required", value=True, category="security", description="Toutes les décisions financières nécessitent validation humaine"),
        Setting(key="max_auto_spend_usd", value=0.0, category="security", description="Dépense maximum automatique sans approbation"),
        Setting(key="product_min_score", value=50.0, category="products", description="Score minimum pour qu'un produit passe en revue"),
        Setting(key="default_markup_pct", value=180.0, category="pricing", description="Markup par défaut sur le prix fournisseur (%)"),
        Setting(key="fraud_auto_reject_score", value=85.0, category="orders", description="Score fraude au-delà duquel la commande est automatiquement rejetée"),
    ]
    for s in settings_data:
        s.created_at = datetime.utcnow()
        s.updated_at = datetime.utcnow()
        db.add(s)
    await db.commit()
    print(f"✓ {len(settings_data)} settings initialized")


async def main():
    print("Starting database seed...")
    print("=" * 50)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        try:
            await seed_roles(db)
            await seed_admin_user(db)
            await seed_departments(db)
            await seed_agents(db)
            await seed_products(db)
            await seed_suppliers(db)
            await seed_connectors(db)
            await seed_settings(db)
            print("=" * 50)
            print("Seed completed successfully!")
            print()
            print("Login credentials:")
            print("  Email: admin@dropship-os.com")
            print("  Password: Admin123!")
            print()
            print("API Documentation: http://localhost:8000/docs")
            print("Dashboard: http://localhost:3000")
        except Exception as e:
            print(f"Seed failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
