"""API contracts for the P2 risk engine (kept separate from P1 contracts.py)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RiskCalculateRequest(BaseModel):
    asset_ids: list[int] | None = Field(
        default=None, description="Restrict calculation to these asset ids; omit for all assets."
    )
    iterations: int | None = Field(
        default=None, ge=1_000, le=500_000, description="Monte Carlo iterations (defaults to config)."
    )
    persist: bool = Field(
        default=True, description="Upsert the P1 risks row and append risk_history snapshots."
    )
    config_overrides: dict[str, Any] | None = Field(
        default=None,
        description="Deep-merged onto RiskEngineConfig (e.g. {'impact': {'breach_cost_per_record_inr': 2500}}).",
    )


class MonteCarloRead(BaseModel):
    iterations: int
    mean: float
    median: float
    p50: float
    p90: float
    p95: float
    p99: float
    var95: float
    var99: float
    probability_of_loss: float
    expected_shortfall_95: float
    max_simulated: float
    percentiles: dict[str, float]


class RiskDriverRead(BaseModel):
    factor: str
    contribution: float
    raw_share_of_likelihood: float | None = None


class ImpactComponentRead(BaseModel):
    factor: str
    amount_inr: float
    contribution: float


class ControlEvaluationRead(BaseModel):
    control_id: int
    name: str
    domain: str | None
    status: str
    base_effectiveness: float
    coverage: float
    effectiveness_score: float
    marginal_eal_reduction_inr: float
    rationale: str


class AssetRiskRead(BaseModel):
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

    p95_loss: float
    p99_loss: float
    var95: float
    var99: float

    risk_drivers: list[RiskDriverRead]


class AssetRiskDetailRead(AssetRiskRead):
    signals: dict[str, Any]
    likelihood_breakdown: dict[str, Any]
    financial_impact_breakdown: dict[str, float]
    impact_drivers: list[ImpactComponentRead]
    monte_carlo: MonteCarloRead
    control_evaluations: list[ControlEvaluationRead]


class GroupRiskRead(BaseModel):
    scope: str
    ref: str
    label: str
    asset_ids: list[int]
    asset_count: int
    expected_annual_loss: float
    residual_expected_annual_loss: float
    p95_loss: float
    p99_loss: float
    var95: float
    var99: float
    monte_carlo: MonteCarloRead
    top_drivers: list[RiskDriverRead]


class EnterpriseRiskRead(BaseModel):
    run_id: str
    generated_at: datetime
    config_version: str
    iterations: int
    total_expected_annual_loss: float
    total_residual_expected_annual_loss: float
    enterprise: GroupRiskRead
    business_services: list[GroupRiskRead]
    departments: list[GroupRiskRead]
    # Backwards-compatible fields mirroring P1's EnterpriseRiskRead shape.
    risk_count: int
    highest_risk_asset_id: int | None
    calculation_version: str


class RiskCalculateResponse(BaseModel):
    run_id: str
    generated_at: datetime
    config_version: str
    iterations: int
    persisted: bool
    assets: list[AssetRiskRead]
    enterprise: GroupRiskRead


class RiskTrendPointRead(BaseModel):
    created_at: datetime
    run_id: str | None
    risk_score: float
    likelihood_score: float
    annual_incident_probability: float
    financial_impact: float
    expected_annual_loss: float
    residual_expected_annual_loss: float
    control_effectiveness: float
    p95_loss: float
    p99_loss: float
    var95: float
    var99: float


class RiskTrendRead(BaseModel):
    scope: str
    ref: str
    label: str | None
    points: list[RiskTrendPointRead]
    delta_expected_annual_loss: float
    note: str
