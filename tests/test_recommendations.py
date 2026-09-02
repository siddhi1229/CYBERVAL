"""
Unit & Integration tests for P4 Recommendation Engine.
Verifies structure, priority ranking, and exact risk reduction calculations.
"""

import unittest
from p1_telemetry.service import P1TelemetryService
from p2_risk_engine.service import P2RiskEngineService
from p3_graph_engine.service import P3GraphEngineService
from p4_ai_decision.recommendation_engine import RecommendationEngine


class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.p1 = P1TelemetryService()
        self.p2 = P2RiskEngineService()
        self.p3 = P3GraphEngineService()
        self.engine = RecommendationEngine(self.p1, self.p2, self.p3)

    def test_recommendation_structure_and_completeness(self):
        recs = self.engine.generate_recommendations()
        self.assertTrue(len(recs) >= 4)

        for r in recs:
            self.assertIn("action", r)
            self.assertIn("reason", r)
            self.assertIn("affected_assets", r)
            self.assertIn("current_risk", r)
            self.assertIn("estimated_risk_after", r)
            self.assertIn("estimated_risk_reduction", r)
            self.assertIn("cost_estimate", r)
            self.assertIn("priority", r)
            self.assertIn("evidence", r)
            
            # Mathematical consistency
            self.assertAlmostEqual(
                r["current_risk"] - r["estimated_risk_reduction"],
                r["estimated_risk_after"],
                delta=0.01,
            )
            self.assertTrue(len(r["evidence"]) > 0)
            self.assertTrue(len(r["affected_assets"]) > 0)

    def test_top_recommendation_is_critical_patch(self):
        recs = self.engine.generate_recommendations()
        top = recs[0]
        self.assertEqual(top["priority"], "CRITICAL")
        self.assertIn("CVE-2024-21413", top["action"])
        self.assertEqual(top["estimated_risk_reduction"], 1180000.0)
        self.assertEqual(top["cost_estimate"], 15000.0)
        self.assertGreater(top["roi_ratio"], 50.0)

    def test_mfa_recommendation_present(self):
        recs = self.engine.generate_recommendations()
        mfa_rec = next((r for r in recs if r["category"] == "MFA"), None)
        self.assertIsNotNone(mfa_rec)
        self.assertEqual(mfa_rec["estimated_risk_reduction"], 800000.0)
        self.assertIn("Payment API", mfa_rec["affected_assets"])
        self.assertIn("Payment Primary Database", mfa_rec["affected_assets"])


if __name__ == "__main__":
    unittest.main()
