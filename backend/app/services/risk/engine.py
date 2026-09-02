"""Risk engine orchestrator.

Pipeline per asset:

    P1 telemetry (signals.py)
        -> control-adjusted factors (controls.py)
        -> likelihood_score + annual_incident_probability (likelihood.py)
        -> financial_impact INR (impact.py)
        -> expected_annual_loss = annual_incident_probability * financial_impact
        -> Monte Carlo annual-loss distribution -> P50/P90/P95/P99 / VaR (monte_carlo.py)
        -> risk_score 0-100, risk drivers (drivers.py)
        -> inherent vs residual EAL + per-control marginal reduction

Portfolio: asset -> business service -> department -> enterprise aggregation,
each asset counted exactly once.

Persistence (opt-in): upserts the existing P1 ``risks`` row per asset and appends
``risk_history`` snapshot rows. No new database; no P1 table altered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
import uuid

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Asset, Control, Risk, Threat, UserAssetAccess
from app.models.risk_history import RiskHistory
from app.services.risk.config import RiskEngineConfig, get_default_config
from app.services.risk.controls import AssetControlAssessment, evaluate_asset_controls
from app.services.risk.drivers import (
    aggregate_drivers,
    compute_impact_drivers,
    compute_risk_drivers,
)
from app.services.risk.impact import FinancialImpact, compute_financial_impact
from app.services.risk.likelihood import LikelihoodResult, compute_likelihood
from app.services.risk.monte_carlo import (
    AssetSimulation,
    MonteCarloResult,
    aggregate_simulations,
    simulate_asset,
    summarize,
)
from app.services.risk.signals import (
    AssetSignals,
    enterprise_threat_baseline,
    extract_asset_signals,
)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _combine(values: list[float]) -> float:
    product = 1.0
    for v in values:
        product *= 1.0 - _clamp(v)
    return _clamp(1.0 - product)


@dataclass
class AssetRiskResult:
    asset_id: int
    asset_code: str | None
    asset_name: str
    criticality: str
    department: str | None
    business_service: str | None

    risk_score: float
    likelihood_score: float
    annual_incident_probability: float
    financial_impact: float
    expected_annual_loss: float

    control_effectiveness: float
    control_weakness: float
    inherent_expected_annual_loss: float
    residual_expected_annual_loss: float
    risk_reduction_from_controls: float

    monte_carlo: MonteCarloResult
    signals: AssetSignals
    likelihood: LikelihoodResult
    impact: FinancialImpact
    risk_drivers: list[dict[str, object]]
    impact_drivers: list[dict[str, object]]
    control_evaluations: list[dict[str, object]]

    _losses: np.ndarray = field(repr=False, default=None)

    @property
    def p95_loss(self) -> float:
        return self.monte_carlo.p95

    @property
    def p99_loss(self) -> float:
        return self.monte_carlo.p99


@dataclass
class GroupRiskResult:
    scope: str
    ref: str
    label: str
    asset_ids: list[int]
    expected_annual_loss: float
    residual_expected_annual_loss: float
    monte_carlo: MonteCarloResult
    top_drivers: list[dict[str, object]]


@dataclass
class PortfolioRiskResult:
    run_id: str
    generated_at: datetime
    config_version: str
    iterations: int
    assets: list[AssetRiskResult]
    business_services: list[GroupRiskResult]
    departments: list[GroupRiskResult]
    enterprise: GroupRiskResult


class RiskEngine:
    def __init__(self, config: RiskEngineConfig | None = None):
        self.config = config or get_default_config()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def _load_assets(self, db: Session, asset_ids: list[int] | None) -> list[Asset]:
        stmt = (
            select(Asset)
            .options(
                selectinload(Asset.business_service),
                selectinload(Asset.vulnerabilities),
                selectinload(Asset.security_events),
                selectinload(Asset.edr_events),
                selectinload(Asset.cspm_findings),
                selectinload(Asset.iam_accesses).selectinload(UserAssetAccess.user),
            )
            .order_by(Asset.id)
        )
        if asset_ids:
            stmt = stmt.where(Asset.id.in_(asset_ids))
        return list(db.scalars(stmt).unique().all())

    # ------------------------------------------------------------------
    # Per-asset
    # ------------------------------------------------------------------
    def calculate_asset(
        self,
        asset: Asset,
        controls: list[Control],
        threat_baseline: float,
        iterations: int | None = None,
        now: datetime | None = None,
    ) -> AssetRiskResult:
        cfg = self.config
        signals = extract_asset_signals(asset, cfg, threat_baseline=threat_baseline, now=now)

        assessment = evaluate_asset_controls(asset, signals, controls, cfg)
        signals.factors["control_weakness"] = assessment.control_weakness

        likelihood = compute_likelihood(signals.factors, cfg)
        impact = compute_financial_impact(asset, signals, cfg)

        residual_eal = likelihood.annual_incident_probability * impact.total

        # Inherent = no credit for controls (control_weakness forced to 1.0).
        inherent_factors = dict(signals.factors)
        inherent_factors["control_weakness"] = 1.0
        inherent_likelihood = compute_likelihood(inherent_factors, cfg)
        inherent_eal = inherent_likelihood.annual_incident_probability * impact.total

        risk_score = self._risk_score(likelihood.likelihood_score, residual_eal)

        sim = simulate_asset(
            asset.id,
            likelihood.annual_incident_probability,
            impact.total,
            cfg,
            iterations=iterations,
        )

        drivers = compute_risk_drivers(signals, likelihood, cfg)
        impact_drivers = compute_impact_drivers(impact)

        control_evals = self._control_evals_with_marginal(
            asset, signals, assessment, impact.total, cfg
        )

        return AssetRiskResult(
            asset_id=asset.id,
            asset_code=asset.asset_id_code,
            asset_name=asset.name,
            criticality=(asset.criticality or "MEDIUM").upper(),
            department=asset.department,
            business_service=asset.business_service.name if asset.business_service else None,
            risk_score=risk_score,
            likelihood_score=round(likelihood.likelihood_score, 5),
            annual_incident_probability=round(likelihood.annual_incident_probability, 5),
            financial_impact=round(impact.total, 2),
            expected_annual_loss=round(residual_eal, 2),
            control_effectiveness=round(assessment.aggregate_effectiveness, 5),
            control_weakness=round(assessment.control_weakness, 5),
            inherent_expected_annual_loss=round(inherent_eal, 2),
            residual_expected_annual_loss=round(residual_eal, 2),
            risk_reduction_from_controls=round(max(inherent_eal - residual_eal, 0.0), 2),
            monte_carlo=sim.result,
            signals=signals,
            likelihood=likelihood,
            impact=impact,
            risk_drivers=drivers,
            impact_drivers=impact_drivers,
            control_evaluations=control_evals,
            _losses=sim.losses,
        )

    def _risk_score(self, likelihood_score: float, expected_annual_loss: float) -> float:
        rc = self.config.risk_score
        impact_index = _clamp(expected_annual_loss / max(rc.eal_reference_inr, 1.0))
        score = 100.0 * (rc.likelihood_weight * likelihood_score + rc.impact_weight * impact_index)
        return round(_clamp(score, 0.0, 100.0), 1)

    def _control_evals_with_marginal(
        self,
        asset: Asset,
        signals: AssetSignals,
        assessment: AssetControlAssessment,
        impact_total: float,
        cfg: RiskEngineConfig,
    ) -> list[dict[str, object]]:
        # Residual EAL with the full control set.
        base_factors = dict(signals.factors)
        base_factors["control_weakness"] = assessment.control_weakness
        base_eal = compute_likelihood(base_factors, cfg).annual_incident_probability * impact_total

        by_domain: dict[str, list[float]] = {}
        for ev in assessment.evaluations:
            if ev.domain:
                by_domain.setdefault(ev.domain, []).append(ev.effectiveness_score)

        out: list[dict[str, object]] = []
        for ev in assessment.evaluations:
            marginal = 0.0
            if ev.domain:
                remaining = [
                    e.effectiveness_score
                    for e in assessment.evaluations
                    if e.domain == ev.domain and e.control_id != ev.control_id
                ]
                new_domain_eff = {d: _combine(v) for d, v in by_domain.items()}
                new_domain_eff[ev.domain] = _combine(remaining)
                new_weakness = _clamp(1.0 - _combine(list(new_domain_eff.values())))
                probe = dict(signals.factors)
                probe["control_weakness"] = new_weakness
                eal_without = compute_likelihood(probe, cfg).annual_incident_probability * impact_total
                marginal = max(eal_without - base_eal, 0.0)
            out.append(
                {
                    "control_id": ev.control_id,
                    "name": ev.name,
                    "domain": ev.domain,
                    "status": ev.status,
                    "base_effectiveness": round(ev.base_effectiveness, 4),
                    "coverage": round(ev.coverage, 4),
                    "effectiveness_score": round(ev.effectiveness_score, 4),
                    "marginal_eal_reduction_inr": round(marginal, 2),
                    "rationale": ev.rationale,
                }
            )
        return out

    # ------------------------------------------------------------------
    # Portfolio
    # ------------------------------------------------------------------
    def calculate_portfolio(
        self,
        db: Session,
        asset_ids: list[int] | None = None,
        iterations: int | None = None,
        persist: bool = False,
        run_id: str | None = None,
        now: datetime | None = None,
    ) -> PortfolioRiskResult:
        now = now or datetime.now(UTC)
        run_id = run_id or uuid.uuid4().hex[:16]
        assets = self._load_assets(db, asset_ids)
        controls = list(db.scalars(select(Control)).all())
        threats = list(db.scalars(select(Threat)).all())
        threat_baseline = enterprise_threat_baseline(threats)

        iters = int(iterations or self.config.monte_carlo.iterations)

        results: list[AssetRiskResult] = [
            self.calculate_asset(a, controls, threat_baseline, iterations=iters, now=now)
            for a in assets
        ]

        sims = {r.asset_id: AssetSimulation(r.asset_id, r._losses, r.monte_carlo) for r in results}

        business_services = self._group(results, sims, "business_service", lambda r: r.business_service)
        departments = self._group(results, sims, "department", lambda r: r.department)
        enterprise = self._enterprise(results, sims)

        portfolio = PortfolioRiskResult(
            run_id=run_id,
            generated_at=now,
            config_version=self.config.version,
            iterations=iters,
            assets=results,
            business_services=business_services,
            departments=departments,
            enterprise=enterprise,
        )

        if persist:
            self._persist(db, portfolio)

        return portfolio

    def _group(self, results, sims, scope, key_fn) -> list[GroupRiskResult]:
        groups: dict[str, list[AssetRiskResult]] = {}
        for r in results:
            key = key_fn(r)
            if not key:
                continue
            groups.setdefault(key, []).append(r)

        out: list[GroupRiskResult] = []
        for key, members in sorted(groups.items()):
            member_sims = [sims[m.asset_id] for m in members]
            mc = aggregate_simulations(member_sims, self.config)
            eal = sum(m.expected_annual_loss for m in members)
            residual = sum(m.residual_expected_annual_loss for m in members)
            drivers = aggregate_drivers([(m.expected_annual_loss, m.risk_drivers) for m in members])
            out.append(
                GroupRiskResult(
                    scope=scope,
                    ref=key,
                    label=key,
                    asset_ids=[m.asset_id for m in members],
                    expected_annual_loss=round(eal, 2),
                    residual_expected_annual_loss=round(residual, 2),
                    monte_carlo=mc,
                    top_drivers=drivers[:8],
                )
            )
        return sorted(out, key=lambda g: g.expected_annual_loss, reverse=True)

    def _enterprise(self, results, sims) -> GroupRiskResult:
        if not results:
            empty = summarize(np.zeros(1), self.config)
            return GroupRiskResult("enterprise", "enterprise", "Enterprise", [], 0.0, 0.0, empty, [])
        mc = aggregate_simulations(list(sims.values()), self.config)
        eal = sum(r.expected_annual_loss for r in results)
        residual = sum(r.residual_expected_annual_loss for r in results)
        drivers = aggregate_drivers([(r.expected_annual_loss, r.risk_drivers) for r in results])
        return GroupRiskResult(
            scope="enterprise",
            ref="enterprise",
            label="Enterprise",
            asset_ids=[r.asset_id for r in results],
            expected_annual_loss=round(eal, 2),
            residual_expected_annual_loss=round(residual, 2),
            monte_carlo=mc,
            top_drivers=drivers[:10],
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _persist(self, db: Session, portfolio: PortfolioRiskResult) -> None:
        existing = {r.asset_id: r for r in db.scalars(select(Risk)).all()}
        for res in portfolio.assets:
            row = existing.get(res.asset_id)
            if row is None:
                row = Risk(asset_id=res.asset_id)
                db.add(row)
            row.likelihood = Decimal(str(round(res.annual_incident_probability, 5)))
            row.financial_impact = Decimal(str(round(res.financial_impact, 2)))
            row.expected_annual_loss = Decimal(str(round(res.expected_annual_loss, 2)))
            row.confidence = Decimal("0.50")  # planning-assumption confidence, not calibrated
            row.calculation_version = self.config.version

            db.add(
                RiskHistory(
                    scope="asset",
                    scope_ref=str(res.asset_id),
                    scope_label=res.asset_name,
                    risk_score=Decimal(str(res.risk_score)),
                    likelihood_score=Decimal(str(round(res.likelihood_score, 5))),
                    annual_incident_probability=Decimal(str(round(res.annual_incident_probability, 5))),
                    financial_impact=Decimal(str(round(res.financial_impact, 2))),
                    expected_annual_loss=Decimal(str(round(res.expected_annual_loss, 2))),
                    control_effectiveness=Decimal(str(round(res.control_effectiveness, 5))),
                    residual_expected_annual_loss=Decimal(str(round(res.residual_expected_annual_loss, 2))),
                    p95_loss=Decimal(str(round(res.monte_carlo.p95, 2))),
                    p99_loss=Decimal(str(round(res.monte_carlo.p99, 2))),
                    var95=Decimal(str(round(res.monte_carlo.var95, 2))),
                    var99=Decimal(str(round(res.monte_carlo.var99, 2))),
                    calculation_version=self.config.version,
                    run_id=portfolio.run_id,
                )
            )

        for group in (*portfolio.business_services, *portfolio.departments, portfolio.enterprise):
            db.add(
                RiskHistory(
                    scope=group.scope,
                    scope_ref=group.ref,
                    scope_label=group.label,
                    risk_score=Decimal("0"),
                    likelihood_score=Decimal("0"),
                    annual_incident_probability=Decimal("0"),
                    financial_impact=Decimal("0"),
                    expected_annual_loss=Decimal(str(round(group.expected_annual_loss, 2))),
                    control_effectiveness=Decimal("0"),
                    residual_expected_annual_loss=Decimal(str(round(group.residual_expected_annual_loss, 2))),
                    p95_loss=Decimal(str(round(group.monte_carlo.p95, 2))),
                    p99_loss=Decimal(str(round(group.monte_carlo.p99, 2))),
                    var95=Decimal(str(round(group.monte_carlo.var95, 2))),
                    var99=Decimal(str(round(group.monte_carlo.var99, 2))),
                    calculation_version=self.config.version,
                    run_id=portfolio.run_id,
                )
            )
        db.commit()
