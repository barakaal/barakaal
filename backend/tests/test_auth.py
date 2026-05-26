import pytest
from httpx import AsyncClient
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@test.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_product_scoring():
    from app.services.product_scoring import ProductScoringService, ProductScoreInput

    svc = ProductScoringService()
    inp = ProductScoreInput(
        demand_score=85,
        growth_rate_pct=50,
        supplier_price_usd=10,
        shipping_cost_usd=2,
        market_avg_price_usd=40,
        shipping_days_max=20,
        competition_level="MEDIUM",
        return_rate_pct=3,
        legal_risk="LOW",
        quality_risk="LOW",
        seasonality_score=70,
        ad_potential="HIGH",
    )
    result = svc.calculate(inp)
    assert 0 <= result.score_final <= 100
    assert result.verdict in ["EXCELLENT", "BON", "MOYEN", "FAIBLE", "REJETÉ"]
    assert result.gross_margin_pct > 0
