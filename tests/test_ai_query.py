"""
Unit & Integration tests for P4 AI Query Engine.
Verifies all mandatory CISO questions and response structures.
"""

import unittest
from p1_telemetry.service import P1TelemetryService
from p2_risk_engine.service import P2RiskEngineService
from p3_graph_engine.service import P3GraphEngineService
from p4_ai_decision.query_engine import AIQueryEngine


class TestAIQueryEngine(unittest.TestCase):

    def setUp(self):
        self.p1 = P1TelemetryService()
        self.p2 = P2RiskEngineService()
        self.p3 = P3GraphEngineService()
        self.engine = AIQueryEngine(self.p1, self.p2, self.p3)

    def test_highest_financial_cyber_risk(self):
        res = self.engine.process_query("What is our highest financial cyber risk?")
        self.assertIn("Payment API", res["answer"])
        self.assertIn("2,054,000", res["answer"])
        self.assertIn("CVE-2024-21413", res["answer"])
        
        # Validate structured fields
        self.assertEqual(len(res["supporting_assets"]), 1)
        self.assertEqual(res["supporting_assets"][0]["asset_id"], "asset-pay-01")
        self.assertEqual(res["financial_metrics"]["asset_expected_annual_loss"], 2054000.0)
        self.assertEqual(res["financial_metrics"]["total_enterprise_eal"], 3420000.0)
        self.assertTrue(len(res["supporting_risks"]) >= 3)
        self.assertTrue(len(res["recommendations"]) > 0)

    def test_why_is_payment_api_risky(self):
        res = self.engine.process_query("Why is Payment API risky?")
        answer = res["answer"]
        
        # Verify 7 core evidence points
        self.assertIn("internet exposed", answer)
        self.assertIn("CVE-2024-21413", answer)
        self.assertIn("MFA", answer)
        self.assertIn("SIEM", answer)
        self.assertIn("EDR", answer)
        self.assertIn("CSPM", answer)
        self.assertIn("Payment Processing", answer)
        
        self.assertEqual(res["supporting_assets"][0]["name"], "Payment API")
        self.assertEqual(res["financial_metrics"]["asset_expected_annual_loss"], 2054000.0)

    def test_which_assets_highest_eal(self):
        res = self.engine.process_query("Which assets have the highest EAL?")
        answer = res["answer"]
        self.assertIn("Payment API", answer)
        self.assertIn("Customer Portal", answer)
        self.assertIn("Payment Primary Database", answer)
        self.assertIn("Analytics & BI Pipeline", answer)
        
        # Check sorting
        assets = res["supporting_assets"]
        self.assertEqual(assets[0]["name"], "Payment API")
        self.assertEqual(assets[0]["expected_annual_loss"], 2054000.0)
        self.assertEqual(assets[1]["name"], "Customer Portal")
        self.assertEqual(assets[1]["expected_annual_loss"], 860000.0)

    def test_vulnerabilities_contributing_losses(self):
        res = self.engine.process_query("Which vulnerabilities contribute most to expected losses?")
        answer = res["answer"]
        self.assertIn("CVE-2024-21413", answer)
        self.assertIn("CVE-2023-4863", answer)
        self.assertIn("1,180,000", answer)

    def test_attack_paths_reaching_critical_services(self):
        res = self.engine.process_query("Which attack paths reach critical business services?")
        answer = res["answer"]
        self.assertIn("AP-PAY-001", answer)
        self.assertIn("Payment Processing", answer)
        self.assertEqual(len(res["supporting_attack_paths"]), 2)

    def test_weakest_controls(self):
        res = self.engine.process_query("Which controls are weakest?")
        answer = res["answer"]
        self.assertIn("CTRL-IAM-01", answer)
        self.assertIn("20%", answer)
        self.assertIn("CTRL-NET-03", answer)

    def test_what_should_we_fix_first(self):
        res = self.engine.process_query("What should we fix first?")
        answer = res["answer"]
        self.assertIn("CVE-2024-21413", answer)
        self.assertIn("1,180,000", answer)
        self.assertEqual(res["financial_metrics"]["estimated_risk_reduction"], 1180000.0)

    def test_security_investment_highest_reduction(self):
        res = self.engine.process_query("What security investment gives the highest risk reduction?")
        self.assertIn("CVE-2024-21413", res["answer"])
        self.assertIn("MFA", res["answer"])
        self.assertTrue(len(res["recommendations"]) >= 3)


if __name__ == "__main__":
    unittest.main()
