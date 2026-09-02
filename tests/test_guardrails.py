"""
Unit & Integration tests for P4 Guardrails & Anti-Hallucination.
Step 9 & Step 10 verification: Missing data handling, non-existent entities, and zero fabrication.
"""

import unittest
from p1_telemetry.service import P1TelemetryService
from p2_risk_engine.service import P2RiskEngineService
from p3_graph_engine.service import P3GraphEngineService
from p4_ai_decision.query_engine import AIQueryEngine
from p4_ai_decision.guardrails import GuardrailValidator


class TestGuardrails(unittest.TestCase):

    def setUp(self):
        self.p1 = P1TelemetryService()
        self.p2 = P2RiskEngineService()
        self.p3 = P3GraphEngineService()
        self.engine = AIQueryEngine(self.p1, self.p2, self.p3)
        self.guardrail = GuardrailValidator(self.p1, self.p2, self.p3)

    def test_missing_asset_query_returns_insufficient_data(self):
        # Querying an entity that does not exist in P1
        res = self.engine.process_query("Why is Quantum Supercluster 99 risky?")
        self.assertIn("Insufficient data", res["answer"])
        self.assertEqual(res.get("guardrail_status"), "TRIGGERED_INSUFFICIENT_DATA")
        self.assertEqual(res["supporting_assets"], [])
        self.assertEqual(res["supporting_risks"], [])

    def test_missing_cve_query_returns_insufficient_data(self):
        res = self.engine.process_query("What is the risk of CVE-9999-88888?")
        self.assertIn("Insufficient data", res["answer"])
        self.assertEqual(res.get("guardrail_status"), "TRIGGERED_INSUFFICIENT_DATA")

    def test_empty_query_returns_insufficient_data(self):
        res = self.engine.process_query("")
        self.assertIn("Insufficient data", res["answer"])

    def test_financial_number_fidelity(self):
        # Verify that reported numbers strictly match P2 calculations
        res = self.engine.process_query("What is our highest financial cyber risk?")
        reported_eal = res["financial_metrics"]["asset_expected_annual_loss"]
        self.assertTrue(self.guardrail.validate_financial_metric("asset-pay-01", reported_eal))


if __name__ == "__main__":
    unittest.main()
