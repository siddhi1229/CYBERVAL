"""Risk-signal extraction layer.

Reads P1 normalized telemetry for a single asset and derives a set of factors,
each normalised to [0, 1], plus raw evidence used for explainability and for the
financial-impact model.

Inputs consumed (all P1, PostgreSQL):
  - Asset (criticality, internet_exposed, business_value, business_service)
  - Vulnerability (cvss_score, severity, known_exploited, known_ransomware_use, status)
  - SecurityEvent / SIEM (event_type, severity, technique, observed_at)
  - EdrEvent (indicator, severity, event_type, raw_payload)
  - CspmFinding (severity, status, internet_exposed, encrypted)
  - User / UserAssetAccess (privileged, mfa_enabled, failed_login_count, risky_login)
  - Threat (annual_frequency) - enterprise threat baseline
  - Control (effectiveness, status) - via controls.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import json

from app.models.entities import Asset, Threat
from app.services.risk.config import RiskEngineConfig

FACTOR_NAMES = (
    "threat_activity",
    "internet_exposure",
    "vulnerability_severity",
    "known_exploitation",
    "identity_risk",
    "endpoint_risk",
    "cloud_posture_risk",
    "control_weakness",
)


@dataclass
class AssetSignals:
    asset_id: int
    asset_code: str | None
    asset_name: str
    factors: dict[str, float]
    evidence: dict[str, object] = field(default_factory=dict)
    criticality_index: float = 0.0
    service_criticality_index: float = 0.0
    active_attack: bool = False
    data_bearing: bool = False
    records_at_risk: float = 0.0
    exfiltration_detected: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "asset_id": self.asset_id,
            "asset_code": self.asset_code,
            "asset_name": self.asset_name,
            "factors": self.factors,
            "evidence": self.evidence,
            "criticality_index": self.criticality_index,
            "service_criticality_index": self.service_criticality_index,
            "active_attack": self.active_attack,
            "data_bearing": self.data_bearing,
            "records_at_risk": self.records_at_risk,
            "exfiltration_detected": self.exfiltration_detected,
        }


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _severity_key(value: str | None) -> str:
    return (value or "medium").strip().lower()


def enterprise_threat_baseline(threats: list[Threat]) -> float:
    """Aggregate enterprise threat pressure from P1 Threat.annual_frequency.

    Uses a 'probability that at least one modelled threat campaign lands' style
    combination: 1 - prod(1 - freq_i), clamped to [0, 1].
    """
    product = 1.0
    for threat in threats:
        try:
            freq = float(threat.annual_frequency or 0.0)
        except (TypeError, ValueError):
            freq = 0.0
        product *= 1.0 - _clamp(freq)
    return _clamp(1.0 - product)


def extract_asset_signals(
    asset: Asset,
    config: RiskEngineConfig,
    threat_baseline: float = 0.0,
    now: datetime | None = None,
) -> AssetSignals:
    cfg = config.signals
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=cfg.siem_lookback_days)

    crit = (asset.criticality or "MEDIUM").strip().upper()
    crit_index = cfg.criticality_index.get(crit, 0.4)

    svc_crit_index = 0.0
    if asset.business_service and asset.business_service.criticality:
        svc_crit_index = cfg.service_criticality_index.get(
            asset.business_service.criticality.strip().lower(), 0.0
        )

    evidence: dict[str, object] = {}

    # ---- internet_exposure -------------------------------------------------
    exposed = bool(asset.internet_exposed)
    cspm_exposed = any(bool(f.internet_exposed) for f in asset.cspm_findings)
    internet_exposure = 0.0
    if exposed:
        internet_exposure = 0.85
    if cspm_exposed:
        internet_exposure = max(internet_exposure, 0.6) + 0.15
    internet_exposure = _clamp(internet_exposure)
    evidence["internet_exposed"] = exposed
    evidence["cspm_internet_exposed_finding"] = cspm_exposed

    # ---- vulnerability_severity & known_exploitation ---------------------
    open_statuses = {s.lower() for s in cfg.open_vuln_statuses}
    open_vulns = [
        v for v in asset.vulnerabilities if (v.status or "open").strip().lower() in open_statuses
    ]
    max_cvss = 0.0
    kev_present = False
    ransomware_present = False
    for v in open_vulns:
        try:
            score = float(v.cvss_score or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        max_cvss = max(max_cvss, score)
        if v.known_exploited:
            kev_present = True
        if getattr(v, "known_ransomware_use", False):
            ransomware_present = True
    vulnerability_severity = _clamp(max_cvss / 10.0)
    known_exploitation = 0.0
    if kev_present:
        known_exploitation = cfg.kev_base
        if ransomware_present:
            known_exploitation += cfg.kev_ransomware_uplift
    known_exploitation = _clamp(known_exploitation)
    evidence["open_vulnerability_count"] = len(open_vulns)
    evidence["max_cvss"] = round(max_cvss, 1)
    evidence["known_exploited_vulnerability"] = kev_present
    evidence["known_ransomware_vulnerability"] = ransomware_present

    # ---- threat_activity (SIEM + enterprise baseline + attacker interest) --
    siem_score = 0.0
    active_attack = False
    recent_siem = 0
    for e in asset.security_events:
        observed = e.observed_at
        if observed is not None:
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=UTC)
            if observed < cutoff:
                continue
        recent_siem += 1
        siem_score += cfg.siem_severity_weight.get(_severity_key(e.severity), 0.4)
        technique = (e.technique or "").upper()
        if any(technique.startswith(t) for t in cfg.siem_active_attack_techniques):
            active_attack = True
    siem_component = _clamp(siem_score / max(cfg.siem_saturation_score, 0.01))
    interest = config.likelihood.criticality_interest.get(crit, 0.25)
    # threat_activity = strongest of: observed SIEM activity, or a baseline built
    # from enterprise threat frequency scaled by attacker interest in this tier.
    threat_activity = _clamp(max(siem_component, threat_baseline * interest))
    evidence["recent_siem_events"] = recent_siem
    evidence["siem_active_attack_technique"] = active_attack

    # ---- endpoint_risk (EDR) -------------------------------------------
    edr_score = 0.0
    exfiltration = False
    high_risk_indicator = False
    for ev in asset.edr_events:
        edr_score += cfg.edr_severity_weight.get(_severity_key(ev.severity), 0.4)
        indicator = (ev.indicator or "").strip().lower()
        if indicator in {i.lower() for i in cfg.edr_high_risk_indicators}:
            high_risk_indicator = True
        if indicator in {"data_staging_for_exfiltration", "data_exfiltration"}:
            exfiltration = True
        records = _records_from_payload(ev.raw_payload)
        if records:
            evidence.setdefault("edr_records_extracted", 0)
            evidence["edr_records_extracted"] = max(int(evidence["edr_records_extracted"]), records)
    endpoint_risk = _clamp(edr_score / max(cfg.edr_saturation_score, 0.01))
    if high_risk_indicator:
        endpoint_risk = max(endpoint_risk, 0.7)
    endpoint_risk = _clamp(endpoint_risk)
    evidence["edr_event_count"] = len(asset.edr_events)
    evidence["edr_high_risk_indicator"] = high_risk_indicator
    if active_attack or high_risk_indicator or exfiltration:
        active_attack = True

    # ---- cloud_posture_risk (CSPM) -----------------------------------
    cspm_score = 0.0
    open_cspm = 0
    for f in asset.cspm_findings:
        if (f.status or "open").strip().lower() not in {"open", "new", "in_progress"}:
            continue
        open_cspm += 1
        weight = cfg.cspm_severity_weight.get(_severity_key(f.severity), 0.4)
        if f.internet_exposed:
            weight += 0.2
        if f.encrypted is False:
            weight += 0.15
        cspm_score += weight
    cloud_posture_risk = _clamp(cspm_score / max(cfg.cspm_saturation_score, 0.01))
    evidence["open_cspm_findings"] = open_cspm

    # ---- identity_risk (IAM) ---------------------------------------
    identity_risk = 0.0
    priv_no_mfa = 0
    risky_logins = 0
    max_failed = 0
    users_seen: set[int] = set()
    for access in asset.iam_accesses:
        user = access.user
        if user is None or user.id in users_seen:
            continue
        users_seen.add(user.id)
        if user.privileged and not user.mfa_enabled:
            priv_no_mfa += 1
        if user.risky_login:
            risky_logins += 1
        max_failed = max(max_failed, int(user.failed_login_count or 0))
    if priv_no_mfa:
        identity_risk += cfg.identity_privileged_no_mfa_weight
    if risky_logins:
        identity_risk += cfg.identity_risky_login_weight
    identity_risk += cfg.identity_failed_login_weight * _clamp(
        max_failed / max(cfg.identity_failed_login_saturation, 1)
    )
    identity_risk = _clamp(identity_risk)
    evidence["privileged_users_without_mfa"] = priv_no_mfa
    evidence["risky_login_users"] = risky_logins
    evidence["max_failed_login_count"] = max_failed

    # ---- control_weakness -----------------------------------------
    # Filled in by the engine after controls.py runs (needs the control set).
    control_weakness = 1.0

    factors = {
        "threat_activity": threat_activity,
        "internet_exposure": internet_exposure,
        "vulnerability_severity": vulnerability_severity,
        "known_exploitation": known_exploitation,
        "identity_risk": identity_risk,
        "endpoint_risk": endpoint_risk,
        "cloud_posture_risk": cloud_posture_risk,
        "control_weakness": control_weakness,
    }

    # ---- data-bearing / records at risk (for financial impact) ------
    asset_type = (asset.asset_type or "").strip().lower()
    default_records = config.impact.records_at_risk_by_type.get(asset_type, 0.0)
    records_at_risk = default_records
    edr_records = float(evidence.get("edr_records_extracted", 0) or 0)
    if edr_records > 0:
        records_at_risk = max(records_at_risk, edr_records)
    if exfiltration and records_at_risk > 0:
        records_at_risk *= config.impact.breach_exfiltration_multiplier
    data_bearing = records_at_risk > 0

    return AssetSignals(
        asset_id=asset.id,
        asset_code=asset.asset_id_code,
        asset_name=asset.name,
        factors=factors,
        evidence=evidence,
        criticality_index=crit_index,
        service_criticality_index=svc_crit_index,
        active_attack=active_attack,
        data_bearing=data_bearing,
        records_at_risk=records_at_risk,
        exfiltration_detected=exfiltration,
    )


def _records_from_payload(raw_payload: str | None) -> int:
    if not raw_payload:
        return 0
    try:
        data = json.loads(raw_payload)
    except (json.JSONDecodeError, TypeError):
        return 0
    for key in ("records_extracted", "records", "record_count", "rows"):
        if key in data:
            try:
                return int(data[key])
            except (TypeError, ValueError):
                return 0
    return 0
