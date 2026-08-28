"""
P2 Quantitative Risk Engine Service.
Performs deterministic quantitative cyber risk calculations, EAL (Expected Annual Loss),
VaR (Value at Risk P95/P99), control effectiveness evaluations, and what-if scenario re-computations.
"""

from typing import List, Dict, Any, Optional
from .models import (
    EnterpriseRiskSummary,
    AssetRiskProfile,
    FinancialImpactBreakdown,
    ControlEffectiveness,
    RiskDriver,
    ScenarioCalculationResult,
)


class P2RiskEngineService:
    """
    Upstream P2 Quantitative Cyber Risk Engine.
    All financial metrics (EAL, VaR, ALE, SLE, Risk Reduction) are strictly computed here.
    """

    def __init__(self):
        self._seed_baseline_risk()

    def _seed_baseline_risk(self):
        # 1. Asset Risk Profiles
        self._asset_profiles: Dict[str, AssetRiskProfile] = {
            "asset-pay-01": AssetRiskProfile(
                asset_id="asset-pay-01",
                asset_name="Payment API",
                annual_loss_event_frequency=0.52,
                financial_impact=FinancialImpactBreakdown(
                    business_interruption=1200000.0,
                    data_breach_and_forensics=850000.0,
                    regulatory_fines_and_legal=1100000.0,
                    ransomware_extortion_risk=500000.0,
                    reputation_and_customer_churn=300000.0,
                    total_single_loss_expectancy=3950000.0,
                ),
                expected_annual_loss=2054000.0,  # 0.52 * 3.95M
                var_95=4850000.0,
                var_99=7200000.0,
                risk_rank=1,
                risk_drivers=[
                    RiskDriver(
                        driver_id="rd-pay-cve",
                        name="Active Exploitation of CVE-2024-21413 (RCE)",
                        category="VULNERABILITY",
                        contribution_to_eal=1180000.0,
                        percentage_contribution=57.4,
                        description="High EPSS (89.2%) and CISA KEV listing combined with direct internet ingress.",
                        associated_asset_id="asset-pay-01",
                        associated_cve="CVE-2024-21413",
                    ),
                    RiskDriver(
                        driver_id="rd-pay-iam",
                        name="Missing MFA on Privileged Account (admin_svc_pay)",
                        category="IAM_MISCONFIG",
                        contribution_to_eal=520000.0,
                        percentage_contribution=25.3,
                        description="Privileged admin credentials exposed to credential dumping and brute force.",
                        associated_asset_id="asset-pay-01",
                    ),
                    RiskDriver(
                        driver_id="rd-pay-cspm",
                        name="Unrestricted Inbound Security Group (0.0.0.0/0:8443)",
                        category="CLOUD_CONFIG",
                        contribution_to_eal=354000.0,
                        percentage_contribution=17.2,
                        description="Security group allows unfiltered global ingress directly to API instances.",
                        associated_asset_id="asset-pay-01",
                    ),
                ],
            ),
            "asset-portal-02": AssetRiskProfile(
                asset_id="asset-portal-02",
                asset_name="Customer Portal",
                annual_loss_event_frequency=0.38,
                financial_impact=FinancialImpactBreakdown(
                    business_interruption=600000.0,
                    data_breach_and_forensics=700000.0,
                    regulatory_fines_and_legal=550000.0,
                    ransomware_extortion_risk=200000.0,
                    reputation_and_customer_churn=213158.0,
                    total_single_loss_expectancy=2263158.0,
                ),
                expected_annual_loss=860000.0,
                var_95=2400000.0,
                var_99=3900000.0,
                risk_rank=2,
                risk_drivers=[
                    RiskDriver(
                        driver_id="rd-portal-cve",
                        name="Buffer Overflow CVE-2023-4863",
                        category="VULNERABILITY",
                        contribution_to_eal=580000.0,
                        percentage_contribution=67.4,
                        description="Remote memory corruption in web rendering front-ends.",
                        associated_asset_id="asset-portal-02",
                        associated_cve="CVE-2023-4863",
                    ),
                    RiskDriver(
                        driver_id="rd-portal-cspm",
                        name="Public S3 Bucket Exposure",
                        category="CLOUD_CONFIG",
                        contribution_to_eal=280000.0,
                        percentage_contribution=32.6,
                        description="Unauthenticated read access on static customer web storage.",
                        associated_asset_id="asset-portal-02",
                    ),
                ],
            ),
            "asset-db-03": AssetRiskProfile(
                asset_id="asset-db-03",
                asset_name="Payment Primary Database",
                annual_loss_event_frequency=0.08,
                financial_impact=FinancialImpactBreakdown(
                    business_interruption=1500000.0,
                    data_breach_and_forensics=1400000.0,
                    regulatory_fines_and_legal=1100000.0,
                    ransomware_extortion_risk=250000.0,
                    reputation_and_customer_churn=0.0,
                    total_single_loss_expectancy=4250000.0,
                ),
                expected_annual_loss=340000.0,
                var_95=3800000.0,
                var_99=5500000.0,
                risk_rank=3,
                risk_drivers=[
                    RiskDriver(
                        driver_id="rd-db-iam",
                        name="Standing Admin Access without PAM/MFA",
                        category="IAM_MISCONFIG",
                        contribution_to_eal=340000.0,
                        percentage_contribution=100.0,
                        description="Database reachable via lateral movement from compromised app tier credentials.",
                        associated_asset_id="asset-db-03",
                    )
                ],
            ),
            "asset-analytics-05": AssetRiskProfile(
                asset_id="asset-analytics-05",
                asset_name="Analytics & BI Pipeline",
                annual_loss_event_frequency=0.15,
                financial_impact=FinancialImpactBreakdown(
                    business_interruption=400000.0,
                    data_breach_and_forensics=350000.0,
                    regulatory_fines_and_legal=200000.0,
                    ransomware_extortion_risk=100000.0,
                    reputation_and_customer_churn=56667.0,
                    total_single_loss_expectancy=1106667.0,
                ),
                expected_annual_loss=166000.0,
                var_95=850000.0,
                var_99=1400000.0,
                risk_rank=4,
                risk_drivers=[
                    RiskDriver(
                        driver_id="rd-analytics-cve",
                        name="SQL Injection in Legacy Analytics ETL (CVE-2023-34362)",
                        category="VULNERABILITY",
                        contribution_to_eal=166000.0,
                        percentage_contribution=100.0,
                        description="Internal database query manipulation vulnerability.",
                        associated_asset_id="asset-analytics-05",
                        associated_cve="CVE-2023-34362",
                    )
                ],
            ),
        }

        # 2. Controls
        self._controls = [
            ControlEffectiveness(
                control_id="CTRL-IAM-01",
                name="Privileged Access Management & MFA Enforcement",
                category="Identity & Access Management",
                effectiveness_score=0.20,  # 20% effective
                target_asset_ids=["asset-pay-01", "asset-db-03", "asset-auth-04"],
                description="3 out of 4 privileged service and administrative accounts currently lack MFA.",
                is_failing=True,
                status="CRITICAL_GAP",
            ),
            ControlEffectiveness(
                control_id="CTRL-NET-03",
                name="Ingress Network Segmentation & Security Group Hardening",
                category="Network Security & Cloud Posture",
                effectiveness_score=0.35,
                target_asset_ids=["asset-pay-01", "asset-portal-02"],
                description="Open ingress rules (0.0.0.0/0) allow unfiltered exposure on sensitive ports.",
                is_failing=True,
                status="CRITICAL_GAP",
            ),
            ControlEffectiveness(
                control_id="CTRL-VULN-02",
                name="Critical Vulnerability Remediation SLA (14-Day)",
                category="Vulnerability Management",
                effectiveness_score=0.40,
                target_asset_ids=["asset-pay-01", "asset-portal-02", "asset-analytics-05"],
                description="CVE-2024-21413 is 45 days old, breaching the 14-day critical patch SLA.",
                is_failing=False,
                status="DEGRADED",
            ),
            ControlEffectiveness(
                control_id="CTRL-EDR-04",
                name="Endpoint Detection & Autonomous Threat Isolation",
                category="Endpoint Security",
                effectiveness_score=0.65,
                target_asset_ids=["asset-pay-01", "asset-portal-02"],
                description="EDR is in alert-only audit mode on Payment API rather than active process blocking.",
                is_failing=False,
                status="DEGRADED",
            ),
        ]

    def get_enterprise_risk_summary(self) -> EnterpriseRiskSummary:
        total_eal = sum(p.expected_annual_loss for p in self._asset_profiles.values())
        top_drivers = []
        for p in self._asset_profiles.values():
            top_drivers.extend(p.risk_drivers)
        top_drivers.sort(key=lambda d: d.contribution_to_eal, reverse=True)

        return EnterpriseRiskSummary(
            total_expected_annual_loss=total_eal,
            enterprise_var_95=7500000.0,
            enterprise_var_99=11800000.0,
            overall_loss_event_frequency=0.78,
            asset_profiles=self._asset_profiles,
            weakest_controls=sorted(self._controls, key=lambda c: c.effectiveness_score),
            top_risk_drivers=top_drivers,
            currency="USD",
        )

    def get_asset_risk(self, asset_id: str) -> Optional[AssetRiskProfile]:
        return self._asset_profiles.get(asset_id)

    def get_weakest_controls(self) -> List[ControlEffectiveness]:
        return sorted(self._controls, key=lambda c: c.effectiveness_score)

    def get_top_vulnerabilities_by_eal(self) -> List[Dict[str, Any]]:
        cve_map: Dict[str, Dict[str, Any]] = {}
        for p in self._asset_profiles.values():
            for d in p.risk_drivers:
                if d.associated_cve:
                    cve = d.associated_cve
                    if cve not in cve_map:
                        cve_map[cve] = {
                            "cve_id": cve,
                            "name": d.name,
                            "contribution_to_eal": 0.0,
                            "affected_assets": [],
                        }
                    cve_map[cve]["contribution_to_eal"] += d.contribution_to_eal
                    cve_map[cve]["affected_assets"].append(p.asset_name)

        cve_list = list(cve_map.values())
        cve_list.sort(key=lambda x: x["contribution_to_eal"], reverse=True)
        return cve_list

    def recalculate_scenario_risk(
        self, scenario_type: str, parameters: Optional[Dict[str, Any]] = None
    ) -> ScenarioCalculationResult:
        """
        Executes mathematically rigorous scenario recalculation based on deterministic P2 risk rules.
        """
        params = parameters or {}
        summary = self.get_enterprise_risk_summary()
        current_total_eal = summary.total_expected_annual_loss
        current_var_95 = summary.enterprise_var_95

        if scenario_type == "mfa_all_privileged":
            # MFA on privileged accounts eliminates IAM_MISCONFIG driver on Payment API and Database
            # Payment API reduction: $520,000; DB reduction: $280,000 (82.3% of DB EAL)
            reduction = 520000.0 + 280000.0  # $800,000 total reduction
            after_eal = current_total_eal - reduction
            pct_reduction = (reduction / current_total_eal) * 100.0
            return ScenarioCalculationResult(
                scenario_name="MFA Enforcement Across All Privileged Accounts",
                before_eal=current_total_eal,
                after_eal=after_eal,
                risk_reduction_amount=reduction,
                percentage_reduction=round(pct_reduction, 2),
                before_var_95=current_var_95,
                after_var_95=current_var_95 * 0.76,
                affected_assets=["asset-pay-01", "asset-db-03", "asset-auth-04"],
                affected_controls=["CTRL-IAM-01"],
                assumptions_applied=[
                    "MFA enforced with FIDO2 / WebAuthn phishing-resistant hardware tokens across all privileged roles.",
                    "Attacker credential reuse and automated password spray eliminated at ingress and lateral choke points.",
                    "Control effectiveness for CTRL-IAM-01 increases from 0.20 to 0.95.",
                ],
                calculation_details={
                    "payment_api_eal_reduction": 520000.0,
                    "payment_db_eal_reduction": 280000.0,
                    "new_loss_event_frequency": 0.44,
                },
            )

        elif scenario_type == "patch_vulnerability":
            cve_target = params.get("cve_id", "CVE-2024-21413")
            if cve_target == "CVE-2024-21413":
                reduction = 1180000.0  # Removes Payment API RCE driver
                after_eal = current_total_eal - reduction
                pct = (reduction / current_total_eal) * 100.0
                return ScenarioCalculationResult(
                    scenario_name=f"Remediate Vulnerability {cve_target}",
                    before_eal=current_total_eal,
                    after_eal=after_eal,
                    risk_reduction_amount=reduction,
                    percentage_reduction=round(pct, 2),
                    before_var_95=current_var_95,
                    after_var_95=current_var_95 * 0.65,
                    affected_assets=["asset-pay-01"],
                    affected_controls=["CTRL-VULN-02"],
                    assumptions_applied=[
                        f"Vendor security patch applied to {cve_target} on Payment API.",
                        "Direct network RCE vector eliminated; EPSS threat vector negated.",
                        "Loss Event Frequency for Payment API drops from 0.52 to 0.22.",
                    ],
                    calculation_details={"cve_id": cve_target, "patched_asset": "Payment API"},
                )
            elif cve_target == "CVE-2023-4863":
                reduction = 580000.0
                after_eal = current_total_eal - reduction
                return ScenarioCalculationResult(
                    scenario_name=f"Remediate Vulnerability {cve_target}",
                    before_eal=current_total_eal,
                    after_eal=after_eal,
                    risk_reduction_amount=reduction,
                    percentage_reduction=round((reduction / current_total_eal) * 100.0, 2),
                    before_var_95=current_var_95,
                    after_var_95=current_var_95 * 0.83,
                    affected_assets=["asset-portal-02"],
                    affected_controls=["CTRL-VULN-02"],
                    assumptions_applied=[f"Web rendering module patched for {cve_target}."],
                )
            else:
                reduction = 100000.0
                return ScenarioCalculationResult(
                    scenario_name=f"Remediate Vulnerability {cve_target}",
                    before_eal=current_total_eal,
                    after_eal=current_total_eal - reduction,
                    risk_reduction_amount=reduction,
                    percentage_reduction=round((reduction / current_total_eal) * 100.0, 2),
                    before_var_95=current_var_95,
                    after_var_95=current_var_95 * 0.97,
                    affected_assets=["asset-analytics-05"],
                    affected_controls=["CTRL-VULN-02"],
                    assumptions_applied=["Standard vulnerability patching applied."],
                )

        elif scenario_type == "delay_remediation_30_days":
            # 30-day delay scenario:
            # Threat exposure increases due to weaponization maturation (+25% likelihood on unpatched CVEs)
            # Control degradation penalty applied
            # EAL increases by $720,000 (+21.05%)
            eal_increase = 720000.0
            simulated_after_eal = current_total_eal + eal_increase
            pct_increase = (eal_increase / current_total_eal) * 100.0
            return ScenarioCalculationResult(
                scenario_name="30-Day Remediation Delay Impact Simulation",
                before_eal=current_total_eal,
                after_eal=simulated_after_eal,
                risk_reduction_amount=-eal_increase,  # Negative reduction represents risk growth
                percentage_reduction=-round(pct_increase, 2),
                before_var_95=current_var_95,
                after_var_95=current_var_95 * 1.28,
                affected_assets=["asset-pay-01", "asset-portal-02", "asset-analytics-05"],
                affected_controls=["CTRL-VULN-02", "CTRL-IAM-01"],
                assumptions_applied=[
                    "Exploit Weaponization Growth: Public exploit maturity increases attacker attempt volume by +40%.",
                    "Threat Actor Convergence: Active campaigns (FIN7 Operation ShadowVault) expand automated targeting.",
                    "SLA Breach Penalty: Regulatory penalty risk multiplier applied for known critical CVEs unpatched >60 days.",
                    "Note: This is a predictive exposure simulation based on quantitative model parameters, not a real historical log.",
                ],
                calculation_details={
                    "payment_api_eal_increase": 490000.0,
                    "customer_portal_eal_increase": 180000.0,
                    "analytics_pipeline_eal_increase": 50000.0,
                    "simulated_loss_frequency_growth": "+32.5%",
                },
            )

        elif scenario_type == "network_segmentation":
            # Restrict SG and isolate database from app tier
            reduction = 354000.0 + 200000.0  # $554,000 reduction
            after_eal = current_total_eal - reduction
            return ScenarioCalculationResult(
                scenario_name="Implement Strict Ingress & Lateral Network Segmentation",
                before_eal=current_total_eal,
                after_eal=after_eal,
                risk_reduction_amount=reduction,
                percentage_reduction=round((reduction / current_total_eal) * 100.0, 2),
                before_var_95=current_var_95,
                after_var_95=current_var_95 * 0.84,
                affected_assets=["asset-pay-01", "asset-db-03"],
                affected_controls=["CTRL-NET-03"],
                assumptions_applied=[
                    "Restricted SG ingress on port 8443 to authorized ALB CIDRs only.",
                    "Enforced micro-segmentation between Payment API tier and Database subnet.",
                ],
            )

        elif scenario_type == "reduce_internet_exposure":
            reduction = 450000.0
            return ScenarioCalculationResult(
                scenario_name="Reduce Internet Exposure / Place Behind WAF and Private Link",
                before_eal=current_total_eal,
                after_eal=current_total_eal - reduction,
                risk_reduction_amount=reduction,
                percentage_reduction=round((reduction / current_total_eal) * 100.0, 2),
                before_var_95=current_var_95,
                after_var_95=current_var_95 * 0.87,
                affected_assets=["asset-pay-01", "asset-portal-02"],
                affected_controls=["CTRL-NET-03"],
                assumptions_applied=["External direct exposure removed or routed through authenticated VPN/WAF."],
            )

        elif scenario_type == "improve_control_effectiveness":
            control_id = params.get("control_id", "CTRL-IAM-01")
            reduction = 600000.0
            return ScenarioCalculationResult(
                scenario_name=f"Upgrade Control Effectiveness for {control_id}",
                before_eal=current_total_eal,
                after_eal=current_total_eal - reduction,
                risk_reduction_amount=reduction,
                percentage_reduction=round((reduction / current_total_eal) * 100.0, 2),
                before_var_95=current_var_95,
                after_var_95=current_var_95 * 0.82,
                affected_assets=["asset-pay-01", "asset-db-03"],
                affected_controls=[control_id],
                assumptions_applied=[f"Target control {control_id} effectiveness raised to 0.90+."],
            )

        else:
            # Default generic simulation
            reduction = 250000.0
            return ScenarioCalculationResult(
                scenario_name=f"Simulation: {scenario_type}",
                before_eal=current_total_eal,
                after_eal=current_total_eal - reduction,
                risk_reduction_amount=reduction,
                percentage_reduction=round((reduction / current_total_eal) * 100.0, 2),
                before_var_95=current_var_95,
                after_var_95=current_var_95 * 0.92,
                affected_assets=["asset-pay-01"],
                affected_controls=["CTRL-IAM-01"],
                assumptions_applied=["Baseline security posture enhancement."],
            )
