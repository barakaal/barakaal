from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .departments import router as departments_router
from .agents import router as agents_router
from .products import router as products_router
from .suppliers import router as suppliers_router
from .orders import router as orders_router
from .campaigns import router as campaigns_router
from .finance import router as finance_router
from .reports import router as reports_router
from .approvals import router as approvals_router
from .audit import router as audit_router
from .dashboard import router as dashboard_router
from .connectors import router as connectors_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(departments_router, prefix="/departments", tags=["Departments"])
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_router.include_router(products_router, prefix="/products", tags=["Products"])
api_router.include_router(suppliers_router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(orders_router, prefix="/orders", tags=["Orders"])
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(finance_router, prefix="/finance", tags=["Finance"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(approvals_router, prefix="/approvals", tags=["Approvals"])
api_router.include_router(audit_router, prefix="/audit", tags=["Audit"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(connectors_router, prefix="/connectors", tags=["Connectors"])
