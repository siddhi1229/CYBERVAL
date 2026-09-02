"""P2 risk-engine API.

These routes are registered before the P1 router in ``app.main`` so the two
``/api/risk/*`` stubs P1 shipped (``/api/risk/enterprise`` and
``/api/risk/assets``) are superseded by the engine-backed implementations here
without editing P1's ``routers.py``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Asset
from app.models.risk_history import RiskHistory
from app.schemas.risk_contracts import (
    AssetRiskDetailRead,
    AssetRiskRead,
    EnterpriseRiskRead,
    GroupRiskRead,
    MonteCarloRead,
    RiskCalculateRequest,
    RiskCalculateResponse,
    RiskDriverRead,
    RiskTrendPointRead,
    RiskTrendRead,
)
from app.services.risk.config import get_default_config
from app.services.risk.engine import (
    AssetRiskResult,
    GroupRiskResult,
    PortfolioRiskResult,
    RiskEngine,
)

risk_router = APIRouter(prefix="/api/risk", tags=["risk (P2)"])


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------
def _mc_read(mc) -> MonteCarloRead:
    return MonteCarloRead(
        iterations=mc.iterations,
        mean=round(mc.mean, 2),
        median=round(mc.median, 2),
        p50=round(mc.p50, 2),
        p90=round(mc.p90, 2),
        p95=round(mc.p95, 2),
        p99=round(mc.p99, 2),
        var95=round(mc.var95, 2),
        var99=round(mc.var99, 2),
        probability_of_loss=round(mc.probability_of_loss, 5),
        expected_shortfall_95=round(mc.expected_shortfall_95, 2),
        max_simulated=round(mc.max_simulated, 2),
        percentiles={k: round(v, 2) for k, v in mc.percentiles.items()},
    )


def _asset_read(r: AssetRiskResult) -> AssetRiskRead:
    return AssetRiskRead(
        asset_id=r.asset_id,
        asset_code=r.asset_code,
        asset_name=r.asset_name,
        criticality=r.criticality,
        department=r.department,
        business_service=r.business_service,
        risk_score=r.risk_score,
        likelihood_score=r.likelihood_score,
        annual_incident_probability=r.annual_incident_probability,
        financial_impact=r.financial_impact,
        expected_annual_loss=r.expected_annual_loss,
        control_effectiveness=r.control_effectiveness,
        control_weakness=r.control_weakness,
        inherent_expected_annual_loss=r.inherent_expected_annual_loss,
        residual_expected_annual_loss=r.residual_expected_annual_loss,
        risk_reduction_from_controls=r.risk_reduction_from_controls,
        p95_loss=round(r.monte_carlo.p95, 2),
        p99_loss=round(r.monte_carlo.p99, 2),
        var95=round(r.monte_carlo.var95, 2),
        var99=round(r.monte_carlo.var99, 2),
        risk_drivers=[RiskDriverRead(**d) for d in r.risk_drivers],
    )


def _asset_detail(r: AssetRiskResult) -> AssetRiskDetailRead:
    base = _asset_read(r).model_dump()
    return AssetRiskDetailRead(
        **base,
        signals=r.signals.as_dict(),
        likelihood_breakdown=r.likelihood.as_dict(),
        financial_impact_breakdown=r.impact.as_dict(),
        impact_drivers=r.impact_drivers,
        monte_carlo=_mc_read(r.monte_carlo),
        control_evaluations=r.control_evaluations,
    )


def _group_read(g: GroupRiskResult) -> GroupRiskRead:
    return GroupRiskRead(
        scope=g.scope,
        ref=g.ref,
        label=g.label,
        asset_ids=g.asset_ids,
        asset_count=len(g.asset_ids),
        expected_annual_loss=g.expected_annual_loss,
        residual_expected_annual_loss=g.residual_expected_annual_loss,
        p95_loss=round(g.monte_carlo.p95, 2),
        p99_loss=round(g.monte_carlo.p99, 2),
        var95=round(g.monte_carlo.var95, 2),
        var99=round(g.monte_carlo.var99, 2),
        monte_carlo=_mc_read(g.monte_carlo),
        top_drivers=[RiskDriverRead(**d) for d in g.top_drivers],
    )


def _engine(overrides: dict | None = None) -> RiskEngine:
    return RiskEngine(get_default_config().merged_with(overrides))


def _enterprise_payload(portfolio: PortfolioRiskResult) -> EnterpriseRiskRead:
    highest = max(portfolio.assets, key=lambda a: a.risk_score, default=None)
    return EnterpriseRiskRead(
        run_id=portfolio.run_id,
        generated_at=portfolio.generated_at,
        config_version=portfolio.config_version,
        iterations=portfolio.iterations,
        total_expected_annual_loss=portfolio.enterprise.expected_annual_loss,
        total_residual_expected_annual_loss=portfolio.enterprise.residual_expected_annual_loss,
        enterprise=_group_read(portfolio.enterprise),
        business_services=[_group_read(g) for g in portfolio.business_services],
        departments=[_group_read(g) for g in portfolio.departments],
        risk_count=len(portfolio.assets),
        highest_risk_asset_id=highest.asset_id if highest else None,
        calculation_version=portfolio.config_version,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@risk_router.post("/calculate", response_model=RiskCalculateResponse, summary="Run the risk engine")
def calculate_risk(request: RiskCalculateRequest, db: Session = Depends(get_db)):
    engine = _engine(request.config_overrides)
    portfolio = engine.calculate_portfolio(
        db,
        asset_ids=request.asset_ids,
        iterations=request.iterations,
        persist=request.persist,
    )
    return RiskCalculateResponse(
        run_id=portfolio.run_id,
        generated_at=portfolio.generated_at,
        config_version=portfolio.config_version,
        iterations=portfolio.iterations,
        persisted=request.persist,
        assets=[_asset_read(r) for r in portfolio.assets],
        enterprise=_group_read(portfolio.enterprise),
    )


@risk_router.get("/assets", response_model=list[AssetRiskRead], summary="Financial risk for every asset")
def risk_assets(
    min_score: float = Query(default=0.0, ge=0, le=100),
    business_service: str | None = Query(default=None),
    department: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    engine = _engine()
    portfolio = engine.calculate_portfolio(
        db, iterations=engine.config.monte_carlo.list_iterations, persist=False
    )
    rows = portfolio.assets
    if business_service:
        rows = [r for r in rows if (r.business_service or "").lower() == business_service.lower()]
    if department:
        rows = [r for r in rows if (r.department or "").lower() == department.lower()]
    rows = [r for r in rows if r.risk_score >= min_score]
    rows.sort(key=lambda r: r.expected_annual_loss, reverse=True)
    return [_asset_read(r) for r in rows[:limit]]


@risk_router.get(
    "/enterprise", response_model=EnterpriseRiskRead, summary="Enterprise / service / department risk"
)
def risk_enterprise(db: Session = Depends(get_db)):
    engine = _engine()
    portfolio = engine.calculate_portfolio(
        db, iterations=engine.config.monte_carlo.list_iterations, persist=False
    )
    return _enterprise_payload(portfolio)


@risk_router.get("/drivers", response_model=list[RiskDriverRead], summary="Top enterprise risk drivers")
def risk_drivers(
    scope: str = Query(default="enterprise", pattern="^(enterprise|high_risk_assets)$"),
    top: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    engine = _engine()
    portfolio = engine.calculate_portfolio(
        db, iterations=engine.config.monte_carlo.list_iterations, persist=False
    )
    if scope == "enterprise":
        drivers = portfolio.enterprise.top_drivers
    else:
        threshold = engine.config.high_risk_score_threshold
        from app.services.risk.drivers import aggregate_drivers

        high = [a for a in portfolio.assets if a.risk_score >= threshold]
        drivers = aggregate_drivers([(a.expected_annual_loss, a.risk_drivers) for a in high])
    return [RiskDriverRead(**d) for d in drivers[:top]]


@risk_router.get(
    "/assets/{asset_id}", response_model=AssetRiskDetailRead, summary="Full risk breakdown for one asset"
)
def risk_asset_detail(
    asset_id: int,
    iterations: int | None = Query(default=None, ge=1_000, le=500_000),
    db: Session = Depends(get_db),
):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    engine = _engine()
    portfolio = engine.calculate_portfolio(
        db, asset_ids=[asset_id], iterations=iterations, persist=False
    )
    if not portfolio.assets:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} produced no risk result")
    return _asset_detail(portfolio.assets[0])


@risk_router.get("/trends", response_model=RiskTrendRead, summary="Historical risk trend from risk_history")
def risk_trends(
    scope: str = Query(default="enterprise", pattern="^(asset|business_service|department|enterprise)$"),
    ref: str | None = Query(
        default=None, description="asset id / service name / department name; ignored for enterprise"
    ),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    resolved_ref = "enterprise" if scope == "enterprise" else (ref or "")
    if scope != "enterprise" and not resolved_ref:
        raise HTTPException(status_code=422, detail=f"'ref' is required for scope '{scope}'")

    stmt = (
        select(RiskHistory)
        .where(RiskHistory.scope == scope, RiskHistory.scope_ref == str(resolved_ref))
        .order_by(RiskHistory.created_at.asc(), RiskHistory.id.asc())
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    points = [
        RiskTrendPointRead(
            created_at=r.created_at,
            run_id=r.run_id,
            risk_score=float(r.risk_score or 0),
            likelihood_score=float(r.likelihood_score or 0),
            annual_incident_probability=float(r.annual_incident_probability or 0),
            financial_impact=float(r.financial_impact or 0),
            expected_annual_loss=float(r.expected_annual_loss or 0),
            residual_expected_annual_loss=float(r.residual_expected_annual_loss or 0),
            control_effectiveness=float(r.control_effectiveness or 0),
            p95_loss=float(r.p95_loss or 0),
            p99_loss=float(r.p99_loss or 0),
            var95=float(r.var95 or 0),
            var99=float(r.var99 or 0),
        )
        for r in rows
    ]
    delta = 0.0
    if len(points) >= 2:
        delta = round(points[-1].expected_annual_loss - points[0].expected_annual_loss, 2)
    note = (
        "Points are snapshots appended by POST /api/risk/calculate. "
        "This is recorded run history, not a statistically modelled forecast."
    )
    label = rows[-1].scope_label if rows else None
    return RiskTrendRead(
        scope=scope, ref=str(resolved_ref), label=label, points=points, delta_expected_annual_loss=delta, note=note
    )
