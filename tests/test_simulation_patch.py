"""
Unit & Integration tests for Patch and Network Segmentation Simulations.
Step 5 verification: Multiple scenario recalculations.
"""

import unittest
from p1_telemetry.service import P1TelemetryService
from p2_risk_engine.service import P2RiskEngineService
from p3_graph_engine.service import P3GraphEngineService
from p4_ai_decision.simulation_engine import SimulationEngine


class TestSimulationPatch(unittest.TestCase):

    def setUp(self):
        self.p1 = P1TelemetryService()
        self.p2 = P2RiskEngineService()
        self.p3 = P3GraphEngineService()
        self.engine = SimulationEngine(self.p1, self.p2, self.p3)

    def test_patch_cve_2024_21413(self):
        res = self.engine.run_simulation("patch_vulnerability", {"cve_id": "CVE-2024-21413"})
        self.assertEqual(res["before_eal"], 3420000.0)
        self.assertEqual(res["after_eal"], 2240000.0)
        self.assertEqual(res["risk_reduction"], 1180000.0)
        self.assertEqual(res["percentage_reduction"], 34.5)
        self.assertIn("Payment API", res["affected_assets"])
        self.assertTrue(len(res["affected_attack_paths"]) > 0)

    def test_patch_cve_2023_4863(self):
        res = self.engine.run_simulation("patch_vulnerability", {"cve_id": "CVE-2023-4863"})
        self.assertEqual(res["before_eal"], 3420000.0)
        self.assertEqual(res["after_eal"], 2840000.0)
        self.assertEqual(res["risk_reduction"], 580000.0)
        self.assertIn("Customer Portal", res["affected_assets"])

    def test_network_segmentation_simulation(self):
        res = self.engine.run_simulation("network_segmentation")
        self.assertEqual(res["risk_reduction"], 554000.0)
        self.assertIn("Payment API", res["affected_assets"])
        self.assertIn("Payment Primary Database", res["affected_assets"])

    def test_reduce_internet_exposure_simulation(self):
        res = self.engine.run_simulation("reduce_internet_exposure")
        self.assertEqual(res["risk_reduction"], 450000.0)
        self.assertIn("Payment API", res["affected_assets"])


if __name__ == "__main__":
    unittest.main()
