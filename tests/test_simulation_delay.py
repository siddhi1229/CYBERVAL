"""
Unit & Integration tests for 30-Day Delay What-If Simulation.
Step 6 verification: Increased exposure, documented assumptions, non-historical disclaimer.
"""

import unittest
from p1_telemetry.service import P1TelemetryService
from p2_risk_engine.service import P2RiskEngineService
from p3_graph_engine.service import P3GraphEngineService
from p4_ai_decision.simulation_engine import SimulationEngine


class TestSimulationDelay(unittest.TestCase):

    def setUp(self):
        self.p1 = P1TelemetryService()
        self.p2 = P2RiskEngineService()
        self.p3 = P3GraphEngineService()
        self.engine = SimulationEngine(self.p1, self.p2, self.p3)

    def test_30_day_delay_simulation_metrics(self):
        res = self.engine.run_simulation("delay_remediation_30_days")
        
        self.assertEqual(res["before_eal"], 3420000.0)
        self.assertEqual(res["after_eal"], 4140000.0)
        self.assertEqual(res["risk_reduction"], -720000.0)  # Negative reduction indicates risk increase
        self.assertEqual(res["percentage_reduction"], -21.05)
        
        # Verify affected assets
        self.assertIn("Payment API", res["affected_assets"])
        self.assertIn("Customer Portal", res["affected_assets"])
        
        # Verify assumptions are documented
        self.assertTrue(len(res["assumptions"]) >= 3)
        self.assertTrue(any("Weaponization" in a for a in res["assumptions"]))
        
        # Verify disclaimer that simulated results are not real historical logs
        self.assertIn("simulation_disclaimer", res)
        self.assertIn("not historical", res["simulation_disclaimer"].lower())

    def test_delay_natural_language_query(self):
        res = self.engine.run_simulation("What happens if remediation is delayed 30 days?")
        self.assertEqual(res["after_eal"], 4140000.0)
        self.assertIn("Payment API", res["affected_assets"])


if __name__ == "__main__":
    unittest.main()
