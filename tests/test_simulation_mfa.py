"""
Unit & Integration tests for MFA What-If Simulation.
Step 7 verification: IAM query, risk recalculation, affected assets & attack paths.
"""

import unittest
from p1_telemetry.service import P1TelemetryService
from p2_risk_engine.service import P2RiskEngineService
from p3_graph_engine.service import P3GraphEngineService
from p4_ai_decision.simulation_engine import SimulationEngine


class TestSimulationMFA(unittest.TestCase):

    def setUp(self):
        self.p1 = P1TelemetryService()
        self.p2 = P2RiskEngineService()
        self.p3 = P3GraphEngineService()
        self.engine = SimulationEngine(self.p1, self.p2, self.p3)

    def test_mfa_simulation_results(self):
        res = self.engine.run_simulation("mfa_all_privileged")
        
        self.assertEqual(res["before_eal"], 3420000.0)
        self.assertEqual(res["after_eal"], 2620000.0)
        self.assertEqual(res["risk_reduction"], 800000.0)
        self.assertEqual(res["percentage_reduction"], 23.39)
        
        # Verify affected assets
        self.assertIn("Payment API", res["affected_assets"])
        self.assertIn("Payment Primary Database", res["affected_assets"])
        
        # Verify remediated accounts from P1
        self.assertTrue(len(res["remediated_privileged_accounts"]) >= 3)
        self.assertTrue(any("admin_svc_pay" in acc for acc in res["remediated_privileged_accounts"]))
        
        # Verify affected attack paths from P3
        self.assertTrue(len(res["affected_attack_paths"]) > 0)
        self.assertEqual(res["affected_attack_paths"][0]["path_id"], "AP-PAY-001")
        
        # Verify assumptions
        self.assertTrue(len(res["assumptions"]) > 0)

    def test_mfa_natural_language_query(self):
        res = self.engine.run_simulation("What happens if we enable MFA across all privileged accounts?")
        self.assertEqual(res["risk_reduction"], 800000.0)
        self.assertIn("Payment API", res["affected_assets"])


if __name__ == "__main__":
    unittest.main()
