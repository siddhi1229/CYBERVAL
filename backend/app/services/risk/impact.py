"""Financial-impact model (all values INR).

financial_impact = downtime_cost
                 + data_breach_cost
                 + recovery_cost
                 + regulatory_cost
                 + business_loss
                 + reputational_loss

Every coefficient comes from ``ImpactConfig`` and is overridable per request.
Derivations are documented in docs/risk-engine.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.models.entities import Asset
from app.services.risk.config import HOURS_PER_YEAR, RiskEngineConfig
from app.services.risk.signals import AssetSignals


@dataclass
class FinancialImpact:
    downtime_cost: float
    data_breach_cost: float
    recovery_cost: float
    regulatory_cost: float
    business_loss: float
    reputational_loss: float
    total: float
    # Assumptions surfaced for explainability.
    downtime_hours: float
    records_at_risk: float
    service_annual_revenue: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)

    def components(self) -> dict[str, float]:
        return {
            "downtime_cost": self.downtime_cost,
            "data_breach_cost": self.data_breach_cost,
            "recovery_cost": self.recovery_cost,
            "regulatory_cost": self.regulatory_cost,
            "business_loss": self.business_loss,
            "reputational_loss": self.reputational_loss,
        }


def _criticality(asset: Asset) -> str:
    return (asset.criticality or "MEDIUM").strip().upper()


def compute_financial_impact(
    asset: Asset, signals: AssetSignals, config: RiskEngineConfig
) -> FinancialImpact:
    cfg = config.impact
    crit = _criticality(asset)

    # ---- Downtime --------------------------------------------------------
    base_hours = cfg.expected_downtime_hours.get(crit, 4.0)
    hours_multiplier = 1.0
    if signals.factors.get("internet_exposure", 0.0) >= 0.6:
        hours_multiplier += cfg.downtime_internet_exposed_uplift
    if signals.active_attack:
        hours_multiplier += cfg.downtime_active_attack_uplift
    hours_multiplier = min(hours_multiplier, cfg.downtime_hours_max_multiplier)
    downtime_hours = base_hours * hours_multiplier
    downtime_cost = downtime_hours * cfg.downtime_cost_per_hour_inr.get(crit, 150_000.0)

    # ---- Data breach ---------------------------------------------------
    records = signals.records_at_risk if signals.data_bearing else 0.0
    data_breach_cost = records * cfg.breach_cost_per_record_inr

    # ---- Recovery ----------------------------------------------------
    try:
        asset_value = float(asset.business_value or 0.0)
    except (TypeError, ValueError):
        asset_value = 0.0
    recovery_cost = max(cfg.recovery_cost_pct_of_asset_value * asset_value, cfg.recovery_cost_min_inr)

    # ---- Regulatory --------------------------------------------------
    svc_crit = "medium"
    if asset.business_service and asset.business_service.criticality:
        svc_crit = asset.business_service.criticality.strip().lower()
    regulatory_cost = cfg.regulatory_cost_by_service_criticality_inr.get(svc_crit, 0.0)
    if cfg.regulatory_requires_data_breach and data_breach_cost <= 0.0:
        regulatory_cost = 0.0

    # ---- Business interruption loss --------------------------------
    if asset.business_service and asset.business_service.annual_revenue:
        try:
            service_revenue = float(asset.business_service.annual_revenue or 0.0)
        except (TypeError, ValueError):
            service_revenue = cfg.default_service_annual_revenue_inr
    else:
        service_revenue = cfg.default_service_annual_revenue_inr
    disruption_days = cfg.business_disruption_days.get(crit, 1.0)
    business_loss = (
        service_revenue * (disruption_days * 24.0 / HOURS_PER_YEAR) * cfg.revenue_dependency_factor
    )

    # ---- Reputational loss ---------------------------------------
    reputational_loss = cfg.reputational_multiplier * (data_breach_cost + business_loss)

    total = (
        downtime_cost
        + data_breach_cost
        + recovery_cost
        + regulatory_cost
        + business_loss
        + reputational_loss
    )

    return FinancialImpact(
        downtime_cost=downtime_cost,
        data_breach_cost=data_breach_cost,
        recovery_cost=recovery_cost,
        regulatory_cost=regulatory_cost,
        business_loss=business_loss,
        reputational_loss=reputational_loss,
        total=total,
        downtime_hours=downtime_hours,
        records_at_risk=records,
        service_annual_revenue=service_revenue,
    )
