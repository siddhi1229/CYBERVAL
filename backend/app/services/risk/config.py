"""Configurable assumptions for the P2 risk engine.

EVERY number a risk calculation depends on lives here. Nothing in the engine is
hardcoded at a call site. All monetary values are INR (Indian Rupees).

None of these values are statistically calibrated against historical incident
data for this enterprise (there is none). They are transparent, documented
planning assumptions. Override them per-request via ``config_overrides`` on
``POST /api/risk/calculate`` or programmatically by constructing
``RiskEngineConfig(**overrides)``.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field

# Criticality tiers used throughout P1 (Asset.criticality is stored upper-case).
CRITICALITY_TIERS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

HOURS_PER_YEAR = 24 * 365


class LikelihoodConfig(BaseModel):
    """Weights and shape parameters for the explainable likelihood model.

    ``factor_weights`` are *relative*; the engine normalises them to sum to 1
    before use, so only their ratios matter. Each underlying factor is itself
    normalised to [0, 1] in ``signals.py``.
    """

    factor_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "threat_activity": 1.0,
            "internet_exposure": 1.4,
            "vulnerability_severity": 1.3,
            "known_exploitation": 1.8,
            "identity_risk": 1.2,
            "endpoint_risk": 1.1,
            "cloud_posture_risk": 0.9,
            "control_weakness": 1.3,
        }
    )

    # Mapping from the 0-1 likelihood_score to an annual incident probability.
    # p_annual = floor + (cap - floor) * likelihood_score ** gamma
    # This is a deliberately simple monotonic transform, NOT a calibrated model.
    annual_probability_floor: float = 0.01
    annual_probability_cap: float = 0.60
    annual_probability_gamma: float = 1.8

    # Business-criticality tier -> baseline "attacker interest" multiplier applied
    # to threat_activity when no direct SIEM signal is present.
    criticality_interest: dict[str, float] = Field(
        default_factory=lambda: {"LOW": 0.10, "MEDIUM": 0.25, "HIGH": 0.55, "CRITICAL": 0.80}
    )


class RiskScoreConfig(BaseModel):
    """0-100 composite risk score = 100 * (w_l * likelihood_score + w_i * impact_index).

    IMPORTANT: risk_score is an ordinal 0-100 index for ranking assets. It is
    NOT a probability and NOT a monetary figure.
    """

    likelihood_weight: float = 0.55
    impact_weight: float = 0.45
    # Expected annual loss (INR) that maps to impact_index == 1.0 (saturation).
    eal_reference_inr: float = 40_000_000.0


class ImpactConfig(BaseModel):
    """Financial-impact assumptions (INR). See docs/risk-engine.md for derivations."""

    # --- Downtime -----------------------------------------------------------
    downtime_cost_per_hour_inr: dict[str, float] = Field(
        default_factory=lambda: {
            "LOW": 25_000.0,
            "MEDIUM": 150_000.0,
            "HIGH": 500_000.0,
            "CRITICAL": 1_200_000.0,
        }
    )
    expected_downtime_hours: dict[str, float] = Field(
        default_factory=lambda: {"LOW": 2.0, "MEDIUM": 4.0, "HIGH": 8.0, "CRITICAL": 12.0}
    )
    # Exposure / active-attack signals extend the outage. Additive multipliers on
    # expected_downtime_hours, capped by downtime_hours_max_multiplier.
    downtime_internet_exposed_uplift: float = 0.35
    downtime_active_attack_uplift: float = 0.75
    downtime_hours_max_multiplier: float = 3.0

    # --- Data breach ------------------------------------------------------
    breach_cost_per_record_inr: float = 1_800.0
    # Default record counts at risk by asset type when telemetry gives no better
    # number. Assets not listed are treated as non-data-bearing (0 records).
    records_at_risk_by_type: dict[str, float] = Field(
        default_factory=lambda: {
            "database": 200_000.0,
            "application": 25_000.0,
            "cloud": 100_000.0,
            "identity": 5_000.0,
        }
    )
    # If EDR/CSPM evidence shows staged exfiltration, scale the record count.
    breach_exfiltration_multiplier: float = 2.0

    # --- Recovery --------------------------------------------------------
    recovery_cost_pct_of_asset_value: float = 0.15
    recovery_cost_min_inr: float = 500_000.0

    # --- Regulatory (India DPDP Act 2023 reference; max penalty INR 250 crore) --
    regulatory_cost_by_service_criticality_inr: dict[str, float] = Field(
        default_factory=lambda: {
            "low": 0.0,
            "medium": 5_000_000.0,
            "high": 20_000_000.0,
            "critical": 50_000_000.0,
        }
    )
    # Regulatory exposure only applies when a data breach is credible.
    regulatory_requires_data_breach: bool = True

    # --- Business interruption loss -------------------------------------
    # Revenue-bearing disruption window (days) during which a fraction of the
    # linked business service's revenue is considered at risk.
    business_disruption_days: dict[str, float] = Field(
        default_factory=lambda: {"LOW": 0.5, "MEDIUM": 1.0, "HIGH": 3.0, "CRITICAL": 5.0}
    )
    revenue_dependency_factor: float = 0.5
    # Fallback annual revenue (INR) when the asset has no linked business service.
    default_service_annual_revenue_inr: float = 50_000_000.0

    # --- Reputational loss --------------------------------------------
    # Modelled as a multiple of (data_breach_cost + business_loss).
    reputational_multiplier: float = 0.40

    # --- Monte Carlo severity distribution ---------------------------
    # Per-event severity ~ Lognormal with median = deterministic total impact and
    # sigma below (log-space standard deviation => fatter right tail).
    severity_lognormal_sigma: float = 0.55
    # Hard cap on a single simulated event as a multiple of the deterministic total.
    severity_cap_multiplier: float = 8.0


class MonteCarloConfig(BaseModel):
    iterations: int = 50_000
    # Lighter run used by list endpoints that score every asset at once.
    list_iterations: int = 20_000
    seed: int = 20240815
    # Annual event frequency model: Poisson(lambda = annual_incident_probability
    # * frequency_scale). With scale 1.0 and p<=0.75 the sim is dominated by 0/1
    # event years, which is appropriate for enterprise assets.
    frequency_scale: float = 1.0
    percentiles: list[float] = Field(default_factory=lambda: [50.0, 90.0, 95.0, 99.0])


class ControlConfig(BaseModel):
    """Control-effectiveness evaluation parameters."""

    status_active_factor: float = 1.0
    status_inactive_factor: float = 0.25
    # Effectiveness is reduced when telemetry shows the control failing in
    # practice (e.g. brute-force events despite an MFA control).
    telemetry_failure_penalty: float = 0.5
    incident_history_penalty: float = 0.3
    # Name fragments -> the signal domain a control mitigates. Used to map P1's
    # free-text Control.name to the factor it reduces.
    control_domain_keywords: dict[str, str] = Field(
        default_factory=lambda: {
            "mfa": "identity_risk",
            "multi-factor": "identity_risk",
            "authentication": "identity_risk",
            "patch": "vulnerability_severity",
            "vulnerability": "vulnerability_severity",
            "segmentation": "internet_exposure",
            "network": "internet_exposure",
            "firewall": "internet_exposure",
            "endpoint": "endpoint_risk",
            "edr": "endpoint_risk",
            "cloud": "cloud_posture_risk",
            "posture": "cloud_posture_risk",
        }
    )


class SignalConfig(BaseModel):
    """Normalisation constants for raw signal extraction."""

    # SIEM: weight per event severity, and the recent-event count that saturates
    # the threat_activity contribution from SIEM.
    siem_severity_weight: dict[str, float] = Field(
        default_factory=lambda: {"low": 0.15, "medium": 0.4, "high": 0.75, "critical": 1.0}
    )
    siem_saturation_score: float = 3.0
    siem_lookback_days: int = 30
    # ATT&CK techniques that indicate hands-on-keyboard / active compromise.
    siem_active_attack_techniques: list[str] = Field(
        default_factory=lambda: ["T1110", "T1071", "T1068", "T1048", "T1021", "T1078"]
    )

    edr_severity_weight: dict[str, float] = Field(
        default_factory=lambda: {"low": 0.15, "medium": 0.4, "high": 0.75, "critical": 1.0}
    )
    edr_high_risk_indicators: list[str] = Field(
        default_factory=lambda: [
            "credential_dumping",
            "data_staging_for_exfiltration",
            "reverse_shell",
            "memory_inspection",
            "scheduled_task_creation",
        ]
    )
    edr_saturation_score: float = 2.0

    cspm_severity_weight: dict[str, float] = Field(
        default_factory=lambda: {"low": 0.15, "medium": 0.4, "high": 0.75, "critical": 1.0}
    )
    cspm_saturation_score: float = 2.0

    # Identity risk contributions (summed then clamped to 1).
    identity_privileged_no_mfa_weight: float = 0.6
    identity_risky_login_weight: float = 0.25
    identity_failed_login_saturation: int = 15
    identity_failed_login_weight: float = 0.3

    criticality_index: dict[str, float] = Field(
        default_factory=lambda: {"LOW": 0.15, "MEDIUM": 0.4, "HIGH": 0.7, "CRITICAL": 1.0}
    )
    service_criticality_index: dict[str, float] = Field(
        default_factory=lambda: {"low": 0.15, "medium": 0.4, "high": 0.7, "critical": 1.0}
    )
    # known_exploitation factor: base for any KEV vuln, plus ransomware uplift.
    kev_base: float = 0.8
    kev_ransomware_uplift: float = 0.2
    # Vulnerability status values that count as "still open".
    open_vuln_statuses: list[str] = Field(
        default_factory=lambda: ["open", "in_progress", "accepted", "new"]
    )


class RiskEngineConfig(BaseModel):
    """Top-level, fully-configurable assumption set for the risk engine."""

    version: str = "p2-risk-engine-1.0"
    signals: SignalConfig = Field(default_factory=SignalConfig)
    likelihood: LikelihoodConfig = Field(default_factory=LikelihoodConfig)
    risk_score: RiskScoreConfig = Field(default_factory=RiskScoreConfig)
    impact: ImpactConfig = Field(default_factory=ImpactConfig)
    monte_carlo: MonteCarloConfig = Field(default_factory=MonteCarloConfig)
    controls: ControlConfig = Field(default_factory=ControlConfig)

    # High-risk asset threshold used by /api/risk/drivers and reporting.
    high_risk_score_threshold: float = 60.0

    def merged_with(self, overrides: dict[str, Any] | None) -> "RiskEngineConfig":
        """Return a new config with a deep-merged override dict applied."""
        if not overrides:
            return self
        base = self.model_dump()
        merged = _deep_merge(base, overrides)
        return RiskEngineConfig.model_validate(merged)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def get_default_config() -> RiskEngineConfig:
    return RiskEngineConfig()
