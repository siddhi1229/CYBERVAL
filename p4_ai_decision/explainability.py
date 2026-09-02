"""
P4 Explainability & Multi-Source Evidence Synthesizer.
Assembles concrete, auditable internal evidence across P1 (Telemetry), P2 (Risk), and P3 (Graph)
for executive and CISO decision explainability.
"""

from typing import List, Dict, Any, Optional


class EvidenceSynthesizer:
    """
    Synthesizes concrete evidence from P1 telemetry, P2 quantitative metrics,
    and P3 attack paths to construct human-understandable, fully grounded explanations.
    """

    def __init__(self, p1_service, p2_service, p3_service):
        self.p1 = p1_service
        self.p2 = p2_service
        self.p3 = p3_service

    def synthesize_asset_evidence(self, asset_id: str) -> List[str]:
        """
        Gathers multi-source evidence for why a specific asset is risky:
        1. Internet exposure status
        2. Known exploited CVEs
        3. Privileged account IAM status & missing MFA
        4. SIEM alerts (brute force, auth anomalies)
        5. EDR detections (credential dumping, unauthorized processes)
        6. CSPM findings (open security groups, exposed storage)
        7. Business service dependency
        """
        evidence_points = []
        asset = self.p1.get_asset(asset_id)
        if not asset:
            return ["Insufficient data: Asset not found in inventory."]

        # 1. Internet Exposure
        if asset.internet_exposed:
            evidence_points.append(f"It is internet exposed (Public IP: {asset.ip_address}).")
        else:
            evidence_points.append(f"It is an internal asset (Private IP: {asset.ip_address}).")

        # 2. Known Exploited CVEs
        vulns = self.p1.get_vulnerabilities_for_asset(asset_id)
        exploited_vulns = [v for v in vulns if v.known_exploited]
        if exploited_vulns:
            cve_strs = [f"{v.cve_id} (CVSS {v.cvss_score}, EPSS {v.epss_score:.1%})" for v in exploited_vulns]
            evidence_points.append(f"It has actively exploited vulnerability in CISA KEV: {', '.join(cve_strs)}.")
        elif vulns:
            cve_strs = [f"{v.cve_id} (CVSS {v.cvss_score})" for v in vulns]
            evidence_points.append(f"It contains unpatched vulnerabilities: {', '.join(cve_strs)}.")

        # 3. Privileged Accounts & Missing MFA
        iam_accounts = self.p1.get_all_iam_accounts()
        unmfa_priv = [
            acc
            for acc in iam_accounts
            if acc.is_privileged and not acc.mfa_enabled and asset_id in acc.assigned_assets
        ]
        if unmfa_priv:
            usernames = [f"'{acc.username}' ({acc.role})" for acc in unmfa_priv]
            evidence_points.append(f"A privileged account lacks MFA: {', '.join(usernames)}.")

        # 4. SIEM Alerts
        siem_alerts = self.p1.get_siem_alerts_for_asset(asset_id)
        if siem_alerts:
            descriptions = [f"{a.alert_type} ({a.event_count} events from {a.source_ip})" for a in siem_alerts]
            evidence_points.append(f"SIEM reports active suspicious telemetry: {'; '.join(descriptions)}.")

        # 5. EDR Telemetry
        edr_telemetry = self.p1.get_edr_telemetry_for_asset(asset_id)
        if edr_telemetry:
            detections = [f"{e.detection_type} ({e.mitre_technique} via {e.process_name})" for e in edr_telemetry]
            evidence_points.append(f"EDR telemetry detects high-severity activity: {'; '.join(detections)}.")

        # 6. CSPM Misconfigurations
        cspm_findings = self.p1.get_cspm_findings_for_asset(asset_id)
        if cspm_findings:
            issues = [f"{f.issue} [{f.compliance_framework}]" for f in cspm_findings]
            evidence_points.append(f"CSPM identifies security misconfigurations: {'; '.join(issues)}.")

        # 7. Business Service Criticality
        service = self.p3.get_business_service(asset.business_service)
        if service:
            evidence_points.append(
                f"It directly supports the critical business service '{service.name}' ({service.tier}), with downtime impact of ${service.financial_loss_per_hour_downtime:,.0f}/hr."
            )
        else:
            evidence_points.append(f"It supports the '{asset.business_service}' business service ({asset.criticality.value}).")

        return evidence_points

    def format_numbered_explanation(self, title: str, evidence_points: List[str]) -> str:
        """
        Formats evidence into a clean, numbered CISO executive explanation.
        """
        lines = [f"{title} because:", ""]
        for idx, pt in enumerate(evidence_points, start=1):
            lines.append(f"{idx}. {pt}")
        return "\n".join(lines)
