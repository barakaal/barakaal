from typing import Any, Dict, List

from pydantic import BaseModel


class CEODashboardStats(BaseModel):
    total_products_active: int
    total_orders_today: int
    revenue_today_usd: float
    revenue_this_week_usd: float
    pending_approvals: int
    active_agents: int
    top_products: List[Dict[str, Any]]
    department_status: List[Dict[str, Any]]
    recent_decisions: List[Dict[str, Any]]
    weekly_revenue_chart: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
