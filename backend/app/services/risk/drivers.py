"""Risk-driver attribution.

For a given asset the likelihood_score is a weighted sum of factors, so each
factor's share of the score is exactly ``normalised_weight * factor_value``.
We relabel those factors into the business-facing driver taxonomy from the P2
brief and split ``identity_risk`` into its observable sub-causes
(``mfa_disabled`` / ``privileged_access`` / ``failed_login_activity``) using the
same sub-weights the signal layer used.

``risk_drivers`` contributions are normalised to sum to 1.0 (they answer
"what is driving the *likelihood* of an incident on this asset"). A separate
``impact_drivers`` breakdown answers "what is driving the *cost*".
"""

from __future__ import annotations

from app.services.risk.config import RiskEngineConfig
from app.services.risk.impact import FinancialImpact
from app.services.risk.likelihood import LikelihoodResult
from app.services.risk.signals import AssetSignals

_FACTOR_LABEL = {
    "threat_activity": "siem_activity",
    "internet_exposure": "internet_exposure",
    "vulnerability_severity": "critical_vulnerability",
    "known_exploitation": "known_exploited_vulnerability",
    "endpoint_risk": "edr_activity",
    "cloud_posture_risk": "cspm_misconfiguration",
    "control_weakness": "control_weakness",
}


def compute_risk_drivers(
    signals: AssetSignals,
    likelihood: LikelihoodResult,
    config: RiskEngineConfig,
    top_n: int | None = None,
) -> list[dict[str, object]]:
    contributions = dict(likelihood.weighted_contributions)
    evidence = signals.evidence

    drivers: dict[str, float] = {}

    for factor, share in contributions.items():
        if share <= 0:
            continue
        if factor == "identity_risk":
            _split_identity(share, evidence, config, drivers)
            continue
        label = _FACTOR_LABEL.get(factor, factor)
        drivers[label] = drivers.get(label, 0.0) + share

    total = sum(drivers.values())
    if total <= 0:
        return []

    ranked = sorted(
        (
            {
                "factor": name,
                "contribution": round(value / total, 4),
                "raw_share_of_likelihood": round(value, 4),
            }
            for name, value in drivers.items()
        ),
        key=lambda d: d["contribution"],
        reverse=True,
    )
    if top_n:
        ranked = ranked[:top_n]
    return ranked


def _split_identity(
    share: float, evidence: dict, config: RiskEngineConfig, drivers: dict[str, float]
) -> None:
    cfg = config.signals
    priv_no_mfa = int(evidence.get("privileged_users_without_mfa", 0) or 0)
    risky = int(evidence.get("risky_login_users", 0) or 0)
    max_failed = int(evidence.get("max_failed_login_count", 0) or 0)

    sub_weights: dict[str, float] = {}
    if priv_no_mfa:
        sub_weights["mfa_disabled"] = cfg.identity_privileged_no_mfa_weight
        sub_weights["privileged_access"] = cfg.identity_privileged_no_mfa_weight * 0.5
    if risky:
        sub_weights["failed_login_activity"] = sub_weights.get(
            "failed_login_activity", 0.0
        ) + cfg.identity_risky_login_weight
    if max_failed:
        frac = min(max_failed / max(cfg.identity_failed_login_saturation, 1), 1.0)
        sub_weights["failed_login_activity"] = sub_weights.get(
            "failed_login_activity", 0.0
        ) + cfg.identity_failed_login_weight * frac

    total_sub = sum(sub_weights.values())
    if total_sub <= 0:
        drivers["identity_risk"] = drivers.get("identity_risk", 0.0) + share
        return
    for name, weight in sub_weights.items():
        drivers[name] = drivers.get(name, 0.0) + share * (weight / total_sub)


def compute_impact_drivers(impact: FinancialImpact) -> list[dict[str, object]]:
    components = impact.components()
    total = sum(components.values())
    if total <= 0:
        return []
    return sorted(
        (
            {"factor": name, "amount_inr": round(value, 2), "contribution": round(value / total, 4)}
            for name, value in components.items()
            if value > 0
        ),
        key=lambda d: d["contribution"],
        reverse=True,
    )


def aggregate_drivers(per_asset_drivers: list[tuple[float, list[dict[str, object]]]]) -> list[dict[str, object]]:
    """Combine drivers across assets, weighting each asset by its EAL (INR)."""
    pool: dict[str, float] = {}
    weight_total = 0.0
    for weight, drivers in per_asset_drivers:
        w = max(weight, 0.0)
        weight_total += w
        for d in drivers:
            pool[d["factor"]] = pool.get(d["factor"], 0.0) + w * float(d["contribution"])
    if weight_total <= 0:
        return []
    ranked = sorted(
        ({"factor": name, "contribution": round(value / weight_total, 4)} for name, value in pool.items()),
        key=lambda d: d["contribution"],
        reverse=True,
    )
    return ranked
