"""
Unit & Integration tests for P4 REST API Router.
Verifies POST /api/ai/query, POST /api/ai/recommend, POST /api/simulation/run, GET /health, GET /api/docs.
"""

import unittest
from p4_ai_decision.api import P4APIService


class TestAPIServer(unittest.TestCase):

    def setUp(self):
        self.api = P4APIService()

    def test_health_endpoint(self):
        res = self.api.handle_health()
        self.assertEqual(res["status"], "HEALTHY")
        self.assertIn("P1_Telemetry", res["upstream_status"])
        self.assertIn("P2_Quantitative_Risk", res["upstream_status"])
        self.assertIn("P3_Graph_Engine", res["upstream_status"])

    def test_docs_endpoint(self):
        res = self.api.handle_docs()
        self.assertEqual(len(res["endpoints"]), 4)

    def test_ai_query_api_valid(self):
        payload = {"question": "What is our highest financial cyber risk?"}
        res = self.api.handle_ai_query(payload)
        self.assertIn("Payment API", res["answer"])
        self.assertIn("financial_metrics", res)
        self.assertEqual(res["financial_metrics"]["asset_expected_annual_loss"], 2054000.0)

    def test_ai_query_api_empty(self):
        payload = {"question": ""}
        res = self.api.handle_ai_query(payload)
        self.assertIn("error", res)
        self.assertIn("Insufficient data", res["answer"])

    def test_ai_recommend_api(self):
        payload = {"limit": 2}
        res = self.api.handle_ai_recommend(payload)
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["recommendations"]), 2)
        self.assertEqual(res["recommendations"][0]["priority"], "CRITICAL")

    def test_simulation_run_api_mfa(self):
        payload = {"scenario": "mfa_all_privileged"}
        res = self.api.handle_simulation_run(payload)
        self.assertEqual(res["risk_reduction"], 800000.0)
        self.assertEqual(res["before_eal"], 3420000.0)
        self.assertEqual(res["after_eal"], 2620000.0)

    def test_simulation_run_api_30_day_delay(self):
        payload = {"question": "What happens if remediation is delayed 30 days?"}
        res = self.api.handle_simulation_run(payload)
        self.assertEqual(res["before_eal"], 3420000.0)
        self.assertEqual(res["after_eal"], 4140000.0)
        self.assertEqual(res["risk_reduction"], -720000.0)


if __name__ == "__main__":
    unittest.main()
