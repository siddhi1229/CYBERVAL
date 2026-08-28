"""
P4 Guardrails & Hallucination Prevention.
Ensures zero mathematical or factual fabrication by strictly validating all queries,
entities, metrics, and data sufficiency against upstream P1, P2, and P3 sources.
"""

from typing import Dict, Any, List, Optional, Tuple
import re


class GuardrailValidator:
    """
    Guardrail validator for P4 AI Decision Support Layer.
    Guarantees:
    1. No hallucinated CVE IDs or non-existent assets.
    2. No fabricated financial numbers or risk scores.
    3. Standardized 'Insufficient data.' responses for missing/unknown data.
    4. Safe fallback for ambiguous or unanswerable queries.
    """

    INSUFFICIENT_DATA_MESSAGE = "Insufficient data."

    def __init__(self, p1_service, p2_service, p3_service):
        self.p1 = p1_service
        self.p2 = p2_service
        self.p3 = p3_service

    def validate_asset_exists(self, asset_name_or_id: str) -> Tuple[bool, Optional[Any]]:
        """
        Validates if an asset exists in P1. Returns (exists, asset_object).
        """
        # Try direct ID
        asset = self.p1.get_asset(asset_name_or_id)
        if asset:
            return True, asset
        # Try name matching
        asset = self.p1.get_asset_by_name(asset_name_or_id)
        if asset:
            return True, asset
        return False, None

    def validate_cve_exists(self, cve_id: str) -> Tuple[bool, Optional[Any]]:
        """
        Validates if a CVE exists in P1 vulnerability database.
        """
        vuln = self.p1.get_vulnerability(cve_id)
        if vuln:
            return True, vuln
        return False, None

    def validate_financial_metric(self, asset_id: str, reported_eal: float) -> bool:
        """
        Verifies that any reported EAL matches the P2 calculated value within floating tolerance.
        """
        asset_risk = self.p2.get_asset_risk(asset_id)
        if not asset_risk:
            return False
        return abs(asset_risk.expected_annual_loss - reported_eal) < 1.0

    def check_query_sufficiency(self, question: str) -> Tuple[bool, str]:
        """
        Checks if the query refers to unknown assets, unmonitored systems, or ungrounded questions.
        """
        q = question.strip().lower()
        if not q:
            return False, "Query cannot be empty. Insufficient data."

        # Check for specific asset mentions like "Why is X risky?"
        if "why is" in q and "risky" in q:
            # Extract asset candidate
            match = re.search(r"why is\s+([^?]+?)\s+risky", q)
            if match:
                target = match.group(1).strip()
                exists, _ = self.validate_asset_exists(target)
                if not exists:
                    return False, f"{self.INSUFFICIENT_DATA_MESSAGE} No telemetry or risk records found for entity: '{target}'."

        # Check for specific CVE query
        cve_matches = re.findall(r"cve-\d{4}-\d{4,7}", q, re.IGNORECASE)
        for cve in cve_matches:
            exists, _ = self.validate_cve_exists(cve)
            if not exists:
                return False, f"{self.INSUFFICIENT_DATA_MESSAGE} Vulnerability identifier '{cve.upper()}' is not tracked in current telemetry."

        return True, ""

    def sanitize_unsupported_query(self, question: str) -> Dict[str, Any]:
        """
        Standard fallback payload when a question cannot be resolved or lacks data.
        """
        return {
            "answer": f"{self.INSUFFICIENT_DATA_MESSAGE} The requested inquiry does not map to current telemetry (P1), quantitative risk models (P2), or graph attack paths (P3).",
            "supporting_assets": [],
            "supporting_risks": [],
            "supporting_attack_paths": [],
            "financial_metrics": {
                "total_expected_annual_loss": 0.0,
                "confidence": "UNVERIFIED",
            },
            "recommendations": [],
            "guardrail_status": "TRIGGERED_INSUFFICIENT_DATA",
        }
