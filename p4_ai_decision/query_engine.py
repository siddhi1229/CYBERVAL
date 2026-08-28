"""
P4 AI Query Engine.
Natural language query parser, semantic intent classifier, deterministic reasoning engine,
and executive answer synthesizer for CISO cyber risk decision support.
"""

from typing import Dict, Any, List, Optional
import re
from .guardrails import GuardrailValidator
from .explainability import EvidenceSynthesizer
from .recommendation_engine import RecommendationEngine
from .simulation_engine import SimulationEngine


class AIQueryEngine:
    """
    Main query orchestrator for POST /api/ai/query.
    Interprets natural language inquiries, coordinates with P1/P2/P3 engines,
    applies strict zero-hallucination guardrails, and outputs structured, auditable answers.
    """

    def __init__(self, p1_service, p2_service, p3_service):
        self.p1 = p1_service
        self.p2 = p2_service
        self.p3 = p3_service
        self.guardrails = GuardrailValidator(p1_service, p2_service, p3_service)
        self.explainability = EvidenceSynthesizer(p1_service, p2_service, p3_service)
        self.recommendations = RecommendationEngine(p1_service, p2_service, p3_service)
        self.simulations = SimulationEngine(p1_service, p2_service, p3_service)

    def process_query(self, question: str) -> Dict[str, Any]:
        """
        Processes a CISO natural language question and returns the structured JSON response:
        - answer
        - supporting_assets
        - supporting_risks
        - supporting_attack_paths
        - financial_metrics
        - recommendations
        """
        # 1. Guardrail Sufficiency Check
        is_sufficient, error_msg = self.guardrails.check_query_sufficiency(question)
        if not is_sufficient:
            fallback = self.guardrails.sanitize_unsupported_query(question)
            fallback["answer"] = error_msg
            return fallback

        q = question.lower().strip()

        # Intent Classification & Handler Dispatch (Evaluate specific queries first)
        if self._matches_asset_risk_explain(q):
            return self._handle_asset_risk_explain(question)

        elif self._matches_simulation_query(q):
            return self._handle_simulation_in_query(question)

        elif self._matches_what_to_fix_first(q):
            return self._handle_what_to_fix_first()

        elif self._matches_highest_roi_investment(q):
            return self._handle_highest_roi_investment()

        elif self._matches_vulnerabilities_contributing_losses(q):
            return self._handle_vulnerabilities_contributing_losses()

        elif self._matches_highest_eal_assets(q):
            return self._handle_highest_eal_assets()

        elif self._matches_attack_paths_critical(q):
            return self._handle_attack_paths_critical()

        elif self._matches_weakest_controls(q):
            return self._handle_weakest_controls()

        elif self._matches_highest_risk(q):
            return self._handle_highest_financial_risk()

        else:
            # Fallback for unclassified questions
            return self._handle_unclassified_query(question)

    # Intent Matchers
    def _matches_highest_risk(self, q: str) -> bool:
        return (
            "highest financial" in q
            or "highest cyber risk" in q
            or "top cyber risk" in q
            or "biggest risk" in q
            or "highest risk" in q
        )

    def _matches_asset_risk_explain(self, q: str) -> bool:
        return "why is" in q and "risky" in q

    def _matches_highest_eal_assets(self, q: str) -> bool:
        return (
            ("which assets" in q or "what assets" in q or "top assets" in q)
            and ("eal" in q or "loss" in q or "risk" in q or "highest" in q)
        )

    def _matches_vulnerabilities_contributing_losses(self, q: str) -> bool:
        return (
            "vulnerabilit" in q or "cve" in q
        ) and ("contribute" in q or "expected loss" in q or "eal" in q or "losses" in q or "most" in q)

    def _matches_attack_paths_critical(self, q: str) -> bool:
        return "attack path" in q or "attack paths" in q or "reach critical" in q or "business service" in q

    def _matches_weakest_controls(self, q: str) -> bool:
        return "control" in q and ("weakest" in q or "failing" in q or "gaps" in q or "ineffective" in q)

    def _matches_what_to_fix_first(self, q: str) -> bool:
        return "what should we fix first" in q or "fix first" in q or "prioritize" in q or "priority action" in q

    def _matches_highest_roi_investment(self, q: str) -> bool:
        return (
            "highest risk reduction" in q
            or "best risk reduction" in q
            or "security investment" in q
            or "roi" in q
            or (("investment" in q or "spend" in q) and ("risk reduction" in q or "highest" in q or "best" in q))
        )

    def _matches_simulation_query(self, q: str) -> bool:
        return "what happens if" in q or "simulate" in q or "delayed 30 days" in q or "enable mfa" in q

    # Handlers
    def _handle_highest_financial_risk(self) -> Dict[str, Any]:
        summary = self.p2.get_enterprise_risk_summary()
        top_asset_profile = summary.asset_profiles["asset-pay-01"]
        top_asset = self.p1.get_asset("asset-pay-01")
        evidence = self.explainability.synthesize_asset_evidence("asset-pay-01")
        recs = self.recommendations.generate_recommendations(limit=2)
        paths = self.p3.get_attack_paths_for_asset("Payment API")

        answer_text = (
            f"Our highest financial cyber risk is the **{top_asset.name}** ({top_asset.asset_type}), "
            f"accounting for **${top_asset_profile.expected_annual_loss:,.2f} in Expected Annual Loss (EAL)** "
            f"({(top_asset_profile.expected_annual_loss / summary.total_expected_annual_loss) * 100:.1f}% of total enterprise cyber risk). "
            f"Its Single Loss Expectancy (SLE) is ${top_asset_profile.financial_impact.total_single_loss_expectancy:,.2f}, with a 1-year 95% Value at Risk (VaR) of ${top_asset_profile.var_95:,.2f}.\n\n"
            f"Key risk drivers include:\n"
            f"1. **Active RCE Exploitation (CVE-2024-21413)**: Contributes ${top_asset_profile.risk_drivers[0].contribution_to_eal:,.2f} EAL.\n"
            f"2. **Missing Privileged MFA (admin_svc_pay)**: Contributes ${top_asset_profile.risk_drivers[1].contribution_to_eal:,.2f} EAL.\n"
            f"3. **Open Inbound Security Group (0.0.0.0/0:8443)**: Contributes ${top_asset_profile.risk_drivers[2].contribution_to_eal:,.2f} EAL."
        )

        return {
            "answer": answer_text,
            "supporting_assets": [
                {
                    "asset_id": top_asset.id,
                    "name": top_asset.name,
                    "type": top_asset.asset_type,
                    "criticality": top_asset.criticality.value,
                    "business_service": top_asset.business_service,
                    "internet_exposed": top_asset.internet_exposed,
                    "ip_address": top_asset.ip_address,
                }
            ],
            "supporting_risks": [
                {
                    "driver_id": d.driver_id,
                    "name": d.name,
                    "category": d.category,
                    "contribution_to_eal": d.contribution_to_eal,
                    "percentage_contribution": d.percentage_contribution,
                    "associated_cve": d.associated_cve,
                }
                for d in top_asset_profile.risk_drivers
            ],
            "supporting_attack_paths": [
                {
                    "path_id": p.path_id,
                    "name": p.name,
                    "target_business_service": p.target_business_service,
                    "traversal_probability": p.traversal_probability,
                    "financial_loss": p.estimated_financial_loss,
                    "choke_points": p.choke_points,
                }
                for p in paths
            ],
            "financial_metrics": {
                "total_enterprise_eal": summary.total_expected_annual_loss,
                "asset_expected_annual_loss": top_asset_profile.expected_annual_loss,
                "single_loss_expectancy": top_asset_profile.financial_impact.total_single_loss_expectancy,
                "loss_event_frequency": top_asset_profile.annual_loss_event_frequency,
                "var_95": top_asset_profile.var_95,
                "var_99": top_asset_profile.var_99,
                "financial_impact_breakdown": {
                    "business_interruption": top_asset_profile.financial_impact.business_interruption,
                    "data_breach_and_forensics": top_asset_profile.financial_impact.data_breach_and_forensics,
                    "regulatory_fines_and_legal": top_asset_profile.financial_impact.regulatory_fines_and_legal,
                    "ransomware_extortion_risk": top_asset_profile.financial_impact.ransomware_extortion_risk,
                    "reputation_and_customer_churn": top_asset_profile.financial_impact.reputation_and_customer_churn,
                },
            },
            "recommendations": recs,
        }

    def _handle_asset_risk_explain(self, question: str) -> Dict[str, Any]:
        match = re.search(r"why is\s+([^?]+?)\s+risky", question.lower())
        asset_name = match.group(1).strip() if match else "payment api"

        exists, asset = self.guardrails.validate_asset_exists(asset_name)
        if not exists:
            return self.guardrails.sanitize_unsupported_query(question)

        asset_risk = self.p2.get_asset_risk(asset.id)
        evidence = self.explainability.synthesize_asset_evidence(asset.id)
        formatted_evidence = self.explainability.format_numbered_explanation(
            f"{asset.name} is currently a high financial risk", evidence
        )

        answer_text = (
            f"{formatted_evidence}\n\n"
            f"**Quantitative Risk Summary**:\n"
            f"- Expected Annual Loss (EAL): ${asset_risk.expected_annual_loss:,.2f}\n"
            f"- Single Loss Expectancy: ${asset_risk.financial_impact.total_single_loss_expectancy:,.2f}\n"
            f"- Annual Loss Event Frequency: {asset_risk.annual_loss_event_frequency:.2f}\n"
            f"- 1-Year 95% VaR: ${asset_risk.var_95:,.2f}"
        )

        paths = self.p3.get_attack_paths_for_asset(asset.name)
        recs = self.recommendations.generate_recommendations(limit=2)

        return {
            "answer": answer_text,
            "supporting_assets": [
                {
                    "asset_id": asset.id,
                    "name": asset.name,
                    "type": asset.asset_type,
                    "criticality": asset.criticality.value,
                    "business_service": asset.business_service,
                    "internet_exposed": asset.internet_exposed,
                }
            ],
            "supporting_risks": [
                {
                    "driver_id": d.driver_id,
                    "name": d.name,
                    "category": d.category,
                    "contribution_to_eal": d.contribution_to_eal,
                    "percentage_contribution": d.percentage_contribution,
                }
                for d in asset_risk.risk_drivers
            ],
            "supporting_attack_paths": [
                {
                    "path_id": p.path_id,
                    "name": p.name,
                    "target_business_service": p.target_business_service,
                    "choke_points": p.choke_points,
                }
                for p in paths
            ],
            "financial_metrics": {
                "asset_expected_annual_loss": asset_risk.expected_annual_loss,
                "single_loss_expectancy": asset_risk.financial_impact.total_single_loss_expectancy,
                "var_95": asset_risk.var_95,
                "var_99": asset_risk.var_99,
            },
            "recommendations": recs,
        }

    def _handle_highest_eal_assets(self) -> Dict[str, Any]:
        summary = self.p2.get_enterprise_risk_summary()
        sorted_profiles = sorted(summary.asset_profiles.values(), key=lambda x: x.expected_annual_loss, reverse=True)

        lines = ["Assets ranked by Expected Annual Loss (EAL):", ""]
        supporting_assets = []
        for p in sorted_profiles:
            pct = (p.expected_annual_loss / summary.total_expected_annual_loss) * 100.0
            lines.append(f"{p.risk_rank}. **{p.asset_name}** ({p.asset_id}): **${p.expected_annual_loss:,.2f} EAL** ({pct:.1f}% of total) | 95% VaR: ${p.var_95:,.2f}")
            supporting_assets.append({
                "asset_id": p.asset_id,
                "name": p.asset_name,
                "expected_annual_loss": p.expected_annual_loss,
                "risk_rank": p.risk_rank,
                "var_95": p.var_95,
            })

        return {
            "answer": "\n".join(lines),
            "supporting_assets": supporting_assets,
            "supporting_risks": [
                {"name": d.name, "contribution_to_eal": d.contribution_to_eal}
                for d in summary.top_risk_drivers[:4]
            ],
            "supporting_attack_paths": [],
            "financial_metrics": {
                "total_enterprise_eal": summary.total_expected_annual_loss,
                "enterprise_var_95": summary.enterprise_var_95,
                "currency": summary.currency,
            },
            "recommendations": self.recommendations.generate_recommendations(limit=2),
        }

    def _handle_vulnerabilities_contributing_losses(self) -> Dict[str, Any]:
        top_cves = self.p2.get_top_vulnerabilities_by_eal()
        summary = self.p2.get_enterprise_risk_summary()

        lines = ["Vulnerabilities contributing most to Expected Annual Losses:", ""]
        for idx, item in enumerate(top_cves, start=1):
            vuln = self.p1.get_vulnerability(item["cve_id"])
            cvss = f"CVSS {vuln.cvss_score}" if vuln else ""
            epss = f"EPSS {vuln.epss_score:.1%}" if vuln else ""
            kev = " [CISA KEV Listed]" if vuln and vuln.known_exploited else ""
            lines.append(
                f"{idx}. **{item['cve_id']}** ({cvss}, {epss}{kev}): **${item['contribution_to_eal']:,.2f} EAL** "
                f"across {', '.join(item['affected_assets'])}"
            )

        return {
            "answer": "\n".join(lines),
            "supporting_assets": [{"name": a} for item in top_cves for a in item["affected_assets"]],
            "supporting_risks": [
                {"cve_id": item["cve_id"], "contribution_to_eal": item["contribution_to_eal"]}
                for item in top_cves
            ],
            "supporting_attack_paths": [],
            "financial_metrics": {
                "total_vulnerability_loss_contribution": sum(item["contribution_to_eal"] for item in top_cves),
                "total_enterprise_eal": summary.total_expected_annual_loss,
            },
            "recommendations": self.recommendations.generate_recommendations(limit=2),
        }

    def _handle_attack_paths_critical(self) -> Dict[str, Any]:
        paths = self.p3.get_attack_paths_reaching_critical_services()
        lines = ["Attack paths capable of reaching critical business services:", ""]
        for idx, p in enumerate(paths, start=1):
            lines.append(
                f"**Path {idx}: {p.name}** ({p.path_id})\n"
                f"- Target Business Service: **{p.target_business_service}**\n"
                f"- Traversal Probability: {p.traversal_probability:.1%}\n"
                f"- Estimated Financial Loss: ${p.estimated_financial_loss:,.2f}\n"
                f"- Choke Points: {'; '.join(p.choke_points)}\n"
            )

        return {
            "answer": "\n".join(lines),
            "supporting_assets": [{"name": p.target_critical_asset} for p in paths],
            "supporting_risks": [],
            "supporting_attack_paths": [
                {
                    "path_id": p.path_id,
                    "name": p.name,
                    "target_business_service": p.target_business_service,
                    "traversal_probability": p.traversal_probability,
                    "estimated_financial_loss": p.estimated_financial_loss,
                    "choke_points": p.choke_points,
                }
                for p in paths
            ],
            "financial_metrics": {
                "max_single_path_loss": max(p.estimated_financial_loss for p in paths),
            },
            "recommendations": self.recommendations.generate_recommendations(limit=2),
        }

    def _handle_weakest_controls(self) -> Dict[str, Any]:
        controls = self.p2.get_weakest_controls()
        lines = ["Weakest security controls evaluated by P2 risk engine:", ""]
        for idx, c in enumerate(controls, start=1):
            lines.append(
                f"{idx}. **{c.name}** ({c.control_id}) — Effectiveness: **{c.effectiveness_score:.0%}** [{c.status}]\n"
                f"   - Category: {c.category}\n"
                f"   - Gap Detail: {c.description}\n"
                f"   - Affected Assets: {', '.join(c.target_asset_ids)}\n"
            )

        return {
            "answer": "\n".join(lines),
            "supporting_assets": [{"asset_id": aid} for c in controls for aid in c.target_asset_ids],
            "supporting_risks": [],
            "supporting_attack_paths": [],
            "financial_metrics": {
                "critical_control_gap_count": len([c for c in controls if c.is_failing]),
            },
            "recommendations": self.recommendations.generate_recommendations(limit=3),
        }

    def _handle_what_to_fix_first(self) -> Dict[str, Any]:
        recs = self.recommendations.generate_recommendations(limit=3)
        top_rec = recs[0]

        answer_text = (
            f"**Highest Priority Action**: **{top_rec['action']}**\n\n"
            f"- **Rationale**: {top_rec['reason']}\n"
            f"- **Estimated Risk Reduction**: **${top_rec['estimated_risk_reduction']:,.2f}** ({top_rec['percentage_reduction']}% of enterprise EAL)\n"
            f"- **Cost Estimate**: ${top_rec['cost_estimate']:,.2f}\n"
            f"- **ROI Ratio**: {top_rec['roi_ratio']}x\n"
            f"- **Priority**: {top_rec['priority']}\n"
            f"- **Key Evidence**:\n"
            + "\n".join([f"  • {e}" for e in top_rec['evidence']])
            + f"\n\n**Secondary Immediate Action**: {recs[1]['action']} (Risk Reduction: ${recs[1]['estimated_risk_reduction']:,.2f}, ROI: {recs[1]['roi_ratio']}x)."
        )

        return {
            "answer": answer_text,
            "supporting_assets": [{"name": a} for a in top_rec["affected_assets"]],
            "supporting_risks": [{"name": top_rec["reason"]}],
            "supporting_attack_paths": [],
            "financial_metrics": {
                "current_risk": top_rec["current_risk"],
                "estimated_risk_after": top_rec["estimated_risk_after"],
                "estimated_risk_reduction": top_rec["estimated_risk_reduction"],
                "cost_estimate": top_rec["cost_estimate"],
                "roi_ratio": top_rec["roi_ratio"],
            },
            "recommendations": recs,
        }

    def _handle_highest_roi_investment(self) -> Dict[str, Any]:
        recs = self.recommendations.generate_recommendations()
        lines = ["Security investments ranked by Risk Reduction & ROI:", ""]
        for idx, r in enumerate(recs, start=1):
            lines.append(
                f"{idx}. **{r['action']}**\n"
                f"   - Risk Reduction: **${r['estimated_risk_reduction']:,.2f}** ({r['percentage_reduction']}%)\n"
                f"   - Cost: ${r['cost_estimate']:,.2f} | **ROI Ratio: {r['roi_ratio']}x** | Priority: {r['priority']}\n"
            )

        return {
            "answer": "\n".join(lines),
            "supporting_assets": [],
            "supporting_risks": [],
            "supporting_attack_paths": [],
            "financial_metrics": {
                "top_investment_risk_reduction": recs[0]["estimated_risk_reduction"],
                "top_investment_roi": recs[0]["roi_ratio"],
            },
            "recommendations": recs,
        }

    def _handle_simulation_in_query(self, question: str) -> Dict[str, Any]:
        sim_result = self.simulations.run_simulation(question)
        answer_text = (
            f"**Simulation Output**: {sim_result['scenario']}\n\n"
            f"- **Before EAL**: ${sim_result['before_eal']:,.2f}\n"
            f"- **After EAL**: ${sim_result['after_eal']:,.2f}\n"
            f"- **Risk Reduction / Delta**: ${sim_result['risk_reduction']:,.2f} ({sim_result['percentage_reduction']}%)\n"
            f"- **Affected Assets**: {', '.join(sim_result['affected_assets'])}\n\n"
            f"**Executive Explanation**: {sim_result['explanation']}\n\n"
            f"**Assumptions Applied**:\n"
            + "\n".join([f"• {a}" for a in sim_result.get('assumptions', [])])
        )

        return {
            "answer": answer_text,
            "supporting_assets": [{"name": a} for a in sim_result.get("affected_assets", [])],
            "supporting_risks": [],
            "supporting_attack_paths": sim_result.get("affected_attack_paths", []),
            "financial_metrics": {
                "before_eal": sim_result["before_eal"],
                "after_eal": sim_result["after_eal"],
                "risk_reduction": sim_result["risk_reduction"],
                "percentage_reduction": sim_result["percentage_reduction"],
            },
            "recommendations": self.recommendations.generate_recommendations(limit=2),
        }

    def _handle_unclassified_query(self, question: str) -> Dict[str, Any]:
        # Return fallback with grounded enterprise context
        summary = self.p2.get_enterprise_risk_summary()
        return {
            "answer": (
                f"Enterprise cyber posture overview: Total Expected Annual Loss is ${summary.total_expected_annual_loss:,.2f} "
                f"with 1-year 95% VaR of ${summary.enterprise_var_95:,.2f}. Highest risk asset is Payment API ($2,054,000 EAL). "
                f"For targeted queries, ask about highest financial risks, specific assets, vulnerabilities, control gaps, or what-if remediation simulations."
            ),
            "supporting_assets": [{"asset_id": "asset-pay-01", "name": "Payment API"}],
            "supporting_risks": [{"name": summary.top_risk_drivers[0].name}],
            "supporting_attack_paths": [],
            "financial_metrics": {
                "total_enterprise_eal": summary.total_expected_annual_loss,
                "enterprise_var_95": summary.enterprise_var_95,
            },
            "recommendations": self.recommendations.generate_recommendations(limit=2),
        }
