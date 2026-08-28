"""
P4 What-If Simulation Engine.
Simulates remediation scenarios, control improvements, and timeline delays (e.g. 30-day delay, MFA rollout)
using deterministic P2 quantitative recalculation and P3 attack path disruption analysis.
"""

from typing import Dict, Any, List, Optional


class SimulationEngine:
    """
    Executes what-if simulations for security leadership.
    Integrates P1 IAM/telemetry, P2 risk recalculation, and P3 attack paths.
    """

    def __init__(self, p1_service, p2_service, p3_service):
        self.p1 = p1_service
        self.p2 = p2_service
        self.p3 = p3_service

    def run_simulation(self, scenario_input: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a what-if simulation by normalized scenario key or natural question.
        """
        params = parameters or {}
        scenario_key = self._normalize_scenario_key(scenario_input)

        if scenario_key == "mfa_all_privileged":
            return self._run_mfa_simulation(params)
        elif scenario_key == "delay_remediation_30_days":
            return self._run_30_day_delay_simulation(params)
        elif scenario_key == "patch_vulnerability":
            return self._run_patch_simulation(params)
        elif scenario_key == "network_segmentation":
            return self._run_network_segmentation_simulation(params)
        elif scenario_key == "reduce_internet_exposure":
            return self._run_reduce_exposure_simulation(params)
        elif scenario_key == "disable_privileged_access":
            return self._run_disable_privileged_simulation(params)
        elif scenario_key == "improve_control_effectiveness":
            return self._run_improve_control_simulation(params)
        else:
            # Fallback to generic simulation
            return self._run_generic_simulation(scenario_input, params)

    def _normalize_scenario_key(self, scenario_input: str) -> str:
        s = scenario_input.lower().strip()
        if "mfa" in s or "multi-factor" in s:
            return "mfa_all_privileged"
        elif "delay" in s or "30 day" in s or "30-day" in s or "postpone" in s:
            return "delay_remediation_30_days"
        elif "patch" in s or "cve" in s or "vulnerability" in s:
            return "patch_vulnerability"
        elif "segment" in s or "firewall" in s or "security group" in s:
            return "network_segmentation"
        elif "internet" in s or "exposure" in s or "external" in s:
            return "reduce_internet_exposure"
        elif "disable privileged" in s or "revoke" in s or "pam" in s:
            return "disable_privileged_access"
        elif "control" in s:
            return "improve_control_effectiveness"
        return scenario_input

    def _run_mfa_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 7: What happens if MFA is implemented across all privileged accounts?
        """
        # 1. Identify un-MFA'd privileged accounts from P1 IAM
        unmfa_accounts = self.p1.get_privileged_accounts_without_mfa()
        account_names = [f"{a.username} ({a.role})" for a in unmfa_accounts]

        # 2. Recalculate risk using P2
        calc_result = self.p2.recalculate_scenario_risk("mfa_all_privileged", params)

        # 3. Identify affected attack paths from P3
        all_paths = self.p3.get_all_attack_paths()
        affected_paths = []
        for path in all_paths:
            for step in path.steps:
                if "admin_svc_pay" in step.to_entity or "credential" in step.action_type.lower() or "mfa" in (step.remediation_control or "").lower():
                    affected_paths.append({
                        "path_id": path.path_id,
                        "name": path.name,
                        "disrupted_step": f"Step {step.step_number}: {step.description}",
                        "target_business_service": path.target_business_service,
                    })
                    break

        # 4. Affected assets
        affected_assets = ["Payment API", "Payment Primary Database", "Internal Auth Service"]

        explanation = (
            f"Implementing MFA across all {len(unmfa_accounts)} privileged accounts eliminates credential-theft pivot vectors. "
            f"Enterprise Expected Annual Loss (EAL) drops from ${calc_result.before_eal:,.2f} to ${calc_result.after_eal:,.2f}, "
            f"achieving a risk reduction of ${calc_result.risk_reduction_amount:,.2f} ({calc_result.percentage_reduction}% reduction)."
        )

        return {
            "scenario": "MFA Enforcement Across All Privileged Accounts",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": affected_assets,
            "affected_attack_paths": affected_paths,
            "remediated_privileged_accounts": account_names,
            "assumptions": calc_result.assumptions_applied,
            "explanation": explanation,
        }

    def _run_30_day_delay_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 6: What happens if remediation is delayed 30 days?
        """
        calc_result = self.p2.recalculate_scenario_risk("delay_remediation_30_days", params)

        all_paths = self.p3.get_all_attack_paths()
        affected_paths = [
            {
                "path_id": p.path_id,
                "name": p.name,
                "impact_note": "Traversal probability increases by +25% due to heightened exploit maturity.",
                "target_business_service": p.target_business_service,
            }
            for p in all_paths
        ]

        explanation = (
            f"SIMULATED FORECAST: Delaying remediation by 30 days increases exposure across unpatched assets. "
            f"Expected Annual Loss (EAL) increases from ${calc_result.before_eal:,.2f} to ${calc_result.after_eal:,.2f} "
            f"(an added financial risk of ${abs(calc_result.risk_reduction_amount):,.2f}, +{abs(calc_result.percentage_reduction)}%). "
            f"Note: This is a mathematical risk exposure model based on threat velocity, not a historical log."
        )

        return {
            "scenario": "30-Day Remediation Delay Impact Simulation",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,  # Negative value indicates risk growth
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": ["Payment API", "Customer Portal", "Analytics & BI Pipeline"],
            "affected_attack_paths": affected_paths,
            "assumptions": calc_result.assumptions_applied,
            "explanation": explanation,
            "simulation_disclaimer": "Simulated projection based on quantitative risk models; not historical data.",
        }

    def _run_patch_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        cve_id = params.get("cve_id", "CVE-2024-21413")
        calc_result = self.p2.recalculate_scenario_risk("patch_vulnerability", {"cve_id": cve_id})

        affected_paths = []
        for path in self.p3.get_all_attack_paths():
            for step in path.steps:
                if cve_id in step.description or cve_id in path.name:
                    affected_paths.append({
                        "path_id": path.path_id,
                        "name": path.name,
                        "disrupted_step": f"Step {step.step_number}: {step.description}",
                        "target_business_service": path.target_business_service,
                    })
                    break

        return {
            "scenario": f"Patch Vulnerability {cve_id}",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": ["Payment API"] if cve_id == "CVE-2024-21413" else ["Customer Portal"],
            "affected_attack_paths": affected_paths,
            "assumptions": calc_result.assumptions_applied,
            "explanation": f"Patching {cve_id} reduces EAL by ${calc_result.risk_reduction_amount:,.2f} ({calc_result.percentage_reduction}% reduction).",
        }

    def _run_network_segmentation_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        calc_result = self.p2.recalculate_scenario_risk("network_segmentation", params)
        return {
            "scenario": "Network Segmentation & Security Group Hardening",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": ["Payment API", "Payment Primary Database"],
            "affected_attack_paths": [
                {"path_id": "AP-PAY-001", "name": "External RCE -> Credential Dump -> Lateral Movement to Payment DB", "disrupted_step": "Step 3: Network Microsegmentation"}
            ],
            "assumptions": calc_result.assumptions_applied,
            "explanation": f"Network segmentation reduces EAL by ${calc_result.risk_reduction_amount:,.2f} ({calc_result.percentage_reduction}% reduction).",
        }

    def _run_reduce_exposure_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        calc_result = self.p2.recalculate_scenario_risk("reduce_internet_exposure", params)
        return {
            "scenario": "Reduce Internet Exposure",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": ["Payment API", "Customer Portal"],
            "affected_attack_paths": [
                {"path_id": "AP-PAY-001", "name": "External Ingress vector negated"},
                {"path_id": "AP-PORTAL-002", "name": "Direct web ingress shielded"},
            ],
            "assumptions": calc_result.assumptions_applied,
            "explanation": f"Reducing internet exposure reduces EAL by ${calc_result.risk_reduction_amount:,.2f} ({calc_result.percentage_reduction}% reduction).",
        }

    def _run_disable_privileged_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        calc_result = self.p2.recalculate_scenario_risk("mfa_all_privileged", params)
        return {
            "scenario": "Disable Standing Privileged Access / Enforce Just-In-Time PAM",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": ["Payment API", "Payment Primary Database"],
            "affected_attack_paths": [{"path_id": "AP-PAY-001", "name": "Standing credential exploitation severed"}],
            "assumptions": ["Standing root/admin privileges removed; access granted via short-lived JIT elevation."],
            "explanation": f"Disabling standing privileged access reduces EAL by ${calc_result.risk_reduction_amount:,.2f}.",
        }

    def _run_improve_control_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ctrl_id = params.get("control_id", "CTRL-IAM-01")
        calc_result = self.p2.recalculate_scenario_risk("improve_control_effectiveness", {"control_id": ctrl_id})
        return {
            "scenario": f"Improve Control Effectiveness for {ctrl_id}",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": ["Payment API", "Payment Primary Database"],
            "affected_attack_paths": [{"path_id": "AP-PAY-001", "name": "Control resilience improved"}],
            "assumptions": calc_result.assumptions_applied,
            "explanation": f"Upgrading control {ctrl_id} reduces EAL by ${calc_result.risk_reduction_amount:,.2f}.",
        }

    def _run_generic_simulation(self, scenario_input: str, params: Dict[str, Any]) -> Dict[str, Any]:
        calc_result = self.p2.recalculate_scenario_risk("generic", params)
        return {
            "scenario": f"Simulation: {scenario_input}",
            "before_eal": calc_result.before_eal,
            "after_eal": calc_result.after_eal,
            "risk_reduction": calc_result.risk_reduction_amount,
            "percentage_reduction": calc_result.percentage_reduction,
            "before_var_95": calc_result.before_var_95,
            "after_var_95": calc_result.after_var_95,
            "affected_assets": ["Payment API"],
            "affected_attack_paths": [],
            "assumptions": calc_result.assumptions_applied,
            "explanation": f"Simulated risk reduction of ${calc_result.risk_reduction_amount:,.2f} ({calc_result.percentage_reduction}% reduction).",
        }
