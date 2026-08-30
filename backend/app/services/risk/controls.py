"""Control-effectiveness evaluation and residual-risk support.

P1 stores ``Control`` rows globally (name, description, effectiveness 0-1,
status) plus ``FrameworkControl`` mappings. Controls are not asset-linked, so
the engine treats every active control as enterprise-wide and maps its
free-text name to the risk-signal domain it mitigates
(``ControlConfig.control_domain_keywords``).

For each control we compute an *evidence-adjusted* effectiveness:

    effectiveness = base
                    * status_factor           (active vs inactive)
                    * coverage                (how much of the domain it covers
                                               for THIS asset, from P1 telemetry)
                    * (1 - telemetry_penalty) (control observed failing in practice)
                    * (1 - incident_penalty)  (relevant incident already occurred)

Domain effectiveness combines controls in the same domain with a
defence-in-depth rule: 1 - prod(1 - e_i).

Aggregate asset control effectiveness combines the domain effectiveness values
the same way. ``control_weakness`` (a likelihood factor) = 1 - aggregate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.entities import Asset, Control
from app.services.risk.config import RiskEngineConfig
from app.services.risk.signals import AssetSignals


@dataclass
class ControlEvaluation:
    control_id: int
    name: str
    domain: str | None
    status: str
    base_effectiveness: float
    coverage: float
    telemetry_penalty: float
    incident_penalty: float
    effectiveness_score: float
    rationale: str


@dataclass
class AssetControlAssessment:
    evaluations: list[ControlEvaluation]
    domain_effectiveness: dict[str, float]
    aggregate_effectiveness: float
    control_weakness: float
    # marginal risk-reduction contribution of each control (fraction of the
    # asset's controlled EAL that would return if the control were removed);
    # filled in by the engine which owns the EAL computation.
    marginal_reduction_inr: dict[int, float] = field(default_factory=dict)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _domain_for(name: str, cfg: RiskEngineConfig) -> str | None:
    lowered = (name or "").lower()
    for fragment, domain in cfg.controls.control_domain_keywords.items():
        if fragment in lowered:
            return domain
    return None


def _coverage_for_domain(domain: str, asset: Asset, signals: AssetSignals) -> tuple[float, str]:
    """Heuristic coverage of a control domain for this asset, from P1 evidence."""
    ev = signals.evidence
    if domain == "identity_risk":
        priv_no_mfa = int(ev.get("privileged_users_without_mfa", 0) or 0)
        total_priv = 0
        for access in asset.iam_accesses:
            u = access.user
            if u and u.privileged:
                total_priv += 1
        if total_priv == 0:
            return 0.85, "no privileged access paths to cover"
        covered = _clamp((total_priv - priv_no_mfa) / total_priv)
        return covered, f"{total_priv - priv_no_mfa}/{total_priv} privileged users enrolled in MFA"
    if domain == "vulnerability_severity":
        open_vulns = int(ev.get("open_vulnerability_count", 0) or 0)
        kev = bool(ev.get("known_exploited_vulnerability", False))
        if open_vulns == 0:
            return 0.9, "no open vulnerabilities on asset"
        base = 0.3 if kev else 0.6
        return base, f"{open_vulns} open vulns, KEV present={kev}"
    if domain == "internet_exposure":
        if bool(ev.get("internet_exposed", False)) or bool(ev.get("cspm_internet_exposed_finding", False)):
            open_sg = int(ev.get("open_cspm_findings", 0) or 0)
            return (0.15 if open_sg else 0.4), "asset internet-exposed; segmentation only partially effective"
        return 0.9, "asset not internet-exposed"
    if domain == "endpoint_risk":
        if bool(ev.get("edr_high_risk_indicator", False)):
            return 0.35, "high-risk EDR indicator present despite endpoint control"
        return 0.75, "no high-risk EDR indicators"
    if domain == "cloud_posture_risk":
        open_cspm = int(ev.get("open_cspm_findings", 0) or 0)
        if open_cspm == 0:
            return 0.85, "no open CSPM findings"
        return _clamp(0.6 - 0.1 * open_cspm), f"{open_cspm} open CSPM findings"
    return 0.5, "generic coverage assumption"


def _telemetry_penalty(domain: str, signals: AssetSignals, cfg: RiskEngineConfig) -> tuple[float, str]:
    ev = signals.evidence
    factor = signals.factors.get(domain, 0.0)
    if domain == "identity_risk" and (
        int(ev.get("privileged_users_without_mfa", 0) or 0) > 0
        or int(ev.get("recent_siem_events", 0) or 0) > 0 and factor > 0.5
    ):
        return cfg.controls.telemetry_failure_penalty, "identity attack activity / MFA gap observed"
    if domain == "vulnerability_severity" and bool(ev.get("known_exploited_vulnerability", False)):
        return cfg.controls.telemetry_failure_penalty, "known-exploited vuln still open"
    if domain == "endpoint_risk" and bool(ev.get("edr_high_risk_indicator", False)):
        return cfg.controls.telemetry_failure_penalty, "active EDR detection"
    if domain == "internet_exposure" and int(ev.get("open_cspm_findings", 0) or 0) > 0 and factor > 0.5:
        return cfg.controls.telemetry_failure_penalty * 0.6, "open exposure misconfiguration"
    return 0.0, ""


def _combine(values: list[float]) -> float:
    product = 1.0
    for v in values:
        product *= 1.0 - _clamp(v)
    return _clamp(1.0 - product)


def evaluate_asset_controls(
    asset: Asset,
    signals: AssetSignals,
    controls: list[Control],
    config: RiskEngineConfig,
) -> AssetControlAssessment:
    cfg = config.controls
    evaluations: list[ControlEvaluation] = []
    by_domain: dict[str, list[float]] = {}

    for control in controls:
        status = (control.status or "active").strip().lower()
        status_factor = cfg.status_active_factor if status == "active" else cfg.status_inactive_factor
        try:
            base = float(control.effectiveness or 0.0)
        except (TypeError, ValueError):
            base = 0.0
        domain = _domain_for(control.name, config)

        if domain is None:
            coverage, cov_reason = 0.4, "control domain not mapped to a risk signal"
            tele_penalty, tele_reason = 0.0, ""
        else:
            coverage, cov_reason = _coverage_for_domain(domain, asset, signals)
            tele_penalty, tele_reason = _telemetry_penalty(domain, signals, config)

        incident_penalty = 0.0
        incident_reason = ""
        if domain and signals.factors.get(domain, 0.0) >= 0.75:
            incident_penalty = cfg.incident_history_penalty
            incident_reason = "severe residual signal in this domain"

        score = base * status_factor * coverage
        score *= 1.0 - _clamp(tele_penalty)
        score *= 1.0 - _clamp(incident_penalty)
        score = _clamp(score)

        rationale_parts = [f"base={base:.2f}", f"status={status}", f"coverage={coverage:.2f} ({cov_reason})"]
        if tele_reason:
            rationale_parts.append(f"telemetry_penalty={tele_penalty:.2f} ({tele_reason})")
        if incident_reason:
            rationale_parts.append(f"incident_penalty={incident_penalty:.2f} ({incident_reason})")

        evaluations.append(
            ControlEvaluation(
                control_id=control.id,
                name=control.name,
                domain=domain,
                status=status,
                base_effectiveness=base,
                coverage=coverage,
                telemetry_penalty=tele_penalty,
                incident_penalty=incident_penalty,
                effectiveness_score=score,
                rationale="; ".join(rationale_parts),
            )
        )
        if domain:
            by_domain.setdefault(domain, []).append(score)

    domain_effectiveness = {d: _combine(v) for d, v in by_domain.items()}
    aggregate = _combine(list(domain_effectiveness.values()))
    control_weakness = _clamp(1.0 - aggregate)

    return AssetControlAssessment(
        evaluations=evaluations,
        domain_effectiveness=domain_effectiveness,
        aggregate_effectiveness=aggregate,
        control_weakness=control_weakness,
    )
