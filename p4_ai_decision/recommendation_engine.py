"""
P4 Actionable Recommendation Engine.
Calculates ROI-prioritized security recommendations with exact P2 before/after risk estimations,
cost-benefit analysis, and multi-source telemetry evidence.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Recommendation:
    action: str
    reason: str
    affected_assets: List[str]
    current_risk: float  # Current Enterprise EAL in USD
    estimated_risk_after: float  # Post-action EAL from P2 in USD
    estimated_risk_reduction: float  # Absolute EAL reduction in USD
    percentage_reduction: float  # Percentage reduction of enterprise EAL
    cost_estimate: float  # Implementation cost in USD
    roi_ratio: float  # Risk Reduction / Cost Estimate
    priority: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    category: str  # "PATCHING", "MFA", "PAM", "NETWORK_SEGMENTATION", "EDR", "CLOUD_CONFIG"
    evidence: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RecommendationEngine:
    """
    Evaluates security posture across P1, P2, and P3 to formulate
    mathematically grounded, ROI-ranked recommendations.
    """

    def __init__(self, p1_service, p2_service, p3_service):
        self.p1 = p1_service
        self.p2 = p2_service
        self.p3 = p3_service

    def generate_recommendations(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Computes all actionable recommendations using P2 scenario calculations.
        Returns them sorted strictly by priority and ROI ratio.
        """
        summary = self.p2.get_enterprise_risk_summary()
        current_eal = summary.total_expected_annual_loss

        recommendations: List[Recommendation] = []

        # 1. Patch CVE-2024-21413 on Payment API
        res_patch_pay = self.p2.recalculate_scenario_risk("patch_vulnerability", {"cve_id": "CVE-2024-21413"})
        recommendations.append(
            Recommendation(
                action="Deploy emergency vendor security patch for CVE-2024-21413 on Payment API",
                reason="Eliminates critical remote code execution flaw actively exploited by FIN7 in the wild.",
                affected_assets=["Payment API"],
                current_risk=current_eal,
                estimated_risk_after=res_patch_pay.after_eal,
                estimated_risk_reduction=res_patch_pay.risk_reduction_amount,
                percentage_reduction=res_patch_pay.percentage_reduction,
                cost_estimate=15000.0,
                roi_ratio=round(res_patch_pay.risk_reduction_amount / 15000.0, 1),
                priority="CRITICAL",
                category="PATCHING",
                evidence=[
                    "Vulnerability CVE-2024-21413 has CVSS 9.8 and high exploit probability (EPSS 89.2%).",
                    "Asset is directly internet exposed on public IP 198.51.100.42.",
                    "Active CISA KEV listing and FIN7 Operation ShadowVault threat actor targeting.",
                    "Directly severs Step 1 in Attack Path AP-PAY-001 protecting Payment Processing service.",
                ],
            )
        )

        # 2. MFA on Privileged Accounts
        res_mfa = self.p2.recalculate_scenario_risk("mfa_all_privileged")
        unmfa_accounts = self.p1.get_privileged_accounts_without_mfa()
        usernames = [f"{a.username} ({a.role})" for a in unmfa_accounts]
        recommendations.append(
            Recommendation(
                action="Enforce phishing-resistant MFA (FIDO2/WebAuthn) across all privileged IAM accounts",
                reason="Neutralizes lateral movement and credential theft vulnerabilities across critical tiers.",
                affected_assets=["Payment API", "Payment Primary Database", "Internal Auth Service"],
                current_risk=current_eal,
                estimated_risk_after=res_mfa.after_eal,
                estimated_risk_reduction=res_mfa.risk_reduction_amount,
                percentage_reduction=res_mfa.percentage_reduction,
                cost_estimate=25000.0,
                roi_ratio=round(res_mfa.risk_reduction_amount / 25000.0, 1),
                priority="CRITICAL",
                category="MFA",
                evidence=[
                    f"P1 IAM reports 3 privileged accounts lacking MFA: {', '.join(usernames)}.",
                    "EDR detected active LSASS credential dumping targeting admin_svc_pay on Payment API.",
                    "Control CTRL-IAM-01 is currently failing at 20% effectiveness.",
                    "Eliminates Step 2 credential pivot in Attack Path AP-PAY-001.",
                ],
            )
        )

        # 3. Network Segmentation & Security Group Hardening
        res_net = self.p2.recalculate_scenario_risk("network_segmentation")
        recommendations.append(
            Recommendation(
                action="Restrict inbound Security Group rules on port 8443 to internal ALB CIDRs",
                reason="Closes public ingress vulnerability and prevents unauthenticated internet scanning.",
                affected_assets=["Payment API", "Payment Primary Database"],
                current_risk=current_eal,
                estimated_risk_after=res_net.after_eal,
                estimated_risk_reduction=res_net.risk_reduction_amount,
                percentage_reduction=res_net.percentage_reduction,
                cost_estimate=10000.0,
                roi_ratio=round(res_net.risk_reduction_amount / 10000.0, 1),
                priority="HIGH",
                category="NETWORK_SEGMENTATION",
                evidence=[
                    "CSPM finding cspm-find-101: Inbound rule allows unrestricted 0.0.0.0/0 ingress on port 8443.",
                    "SIEM alert reports 1,420 automated brute-force requests hitting the API endpoint.",
                    "Control CTRL-NET-03 is currently failing at 35% effectiveness.",
                ],
            )
        )

        # 4. Patch Customer Portal CVE-2023-4863
        res_patch_portal = self.p2.recalculate_scenario_risk("patch_vulnerability", {"cve_id": "CVE-2023-4863"})
        recommendations.append(
            Recommendation(
                action="Patch web rendering heap buffer overflow (CVE-2023-4863) on Customer Portal",
                reason="Prevents remote buffer overflow and memory corruption on customer-facing web services.",
                affected_assets=["Customer Portal"],
                current_risk=current_eal,
                estimated_risk_after=res_patch_portal.after_eal,
                estimated_risk_reduction=res_patch_portal.risk_reduction_amount,
                percentage_reduction=res_patch_portal.percentage_reduction,
                cost_estimate=12000.0,
                roi_ratio=round(res_patch_portal.risk_reduction_amount / 12000.0, 1),
                priority="HIGH",
                category="PATCHING",
                evidence=[
                    "CVE-2023-4863 has CVSS 8.8 and EPSS score of 74.1%.",
                    "Asset supports Tier 2 Customer Banking Web business service.",
                    "Neutralizes initial access step in Attack Path AP-PORTAL-002.",
                ],
            )
        )

        # 5. Enable EDR Autonomous Blocking Mode
        res_edr = self.p2.recalculate_scenario_risk("improve_control_effectiveness", {"control_id": "CTRL-EDR-04"})
        recommendations.append(
            Recommendation(
                action="Upgrade EDR agent configuration from Audit/Alert mode to Autonomous Process Blocking",
                reason="Instantly intercepts and terminates in-memory credential dumping (LSASS) and process injection.",
                affected_assets=["Payment API", "Customer Portal"],
                current_risk=current_eal,
                estimated_risk_after=res_edr.after_eal,
                estimated_risk_reduction=res_edr.risk_reduction_amount,
                percentage_reduction=res_edr.percentage_reduction,
                cost_estimate=8000.0,
                roi_ratio=round(res_edr.risk_reduction_amount / 8000.0, 1),
                priority="HIGH",
                category="EDR",
                evidence=[
                    "EDR telemetry edr-tel-4011 observed LSASS memory read permitted without active blocking.",
                    "Control CTRL-EDR-04 currently operating at degraded 65% effectiveness.",
                ],
            )
        )

        # Sort recommendations: Priority rank (CRITICAL > HIGH > MEDIUM), then ROI ratio descending
        priority_weights = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
        recommendations.sort(
            key=lambda r: (priority_weights.get(r.priority, 0), r.roi_ratio),
            reverse=True,
        )

        result = [r.to_dict() for r in recommendations]
        if limit:
            return result[:limit]
        return result
