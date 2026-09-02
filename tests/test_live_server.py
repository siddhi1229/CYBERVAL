"""
Live Socket & HTTP Server Integration Test.
Launches the P4 HTTP Server and tests all endpoints over loopback TCP socket.
"""

import unittest
import threading
import time
import json
import urllib.request
from p4_ai_decision.server import ThreadedHTTPServer, P4HTTPRequestHandler


class TestLiveHTTPServer(unittest.TestCase):
    server = None
    server_thread = None
    port = 8899

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadedHTTPServer(("127.0.0.1", cls.port), P4HTTPRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def _post(self, path: str, payload: dict) -> dict:
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path: str) -> dict:
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_live_get_health(self):
        data = self._get("/health")
        self.assertEqual(data["status"], "HEALTHY")
        self.assertIn("P4 — AI Decision Support Layer", data["service"])

    def test_live_get_docs(self):
        data = self._get("/api/docs")
        self.assertIn("endpoints", data)
        self.assertTrue(len(data["endpoints"]) >= 4)

    def test_live_post_ai_query(self):
        payload = {"question": "What is our highest financial cyber risk?"}
        data = self._post("/api/ai/query", payload)
        self.assertIn("Payment API", data["answer"])
        self.assertEqual(data["financial_metrics"]["asset_expected_annual_loss"], 2054000.0)

    def test_live_post_ai_recommend(self):
        payload = {"limit": 3}
        data = self._post("/api/ai/recommend", payload)
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["recommendations"]), 3)

    def test_live_post_simulation_run_mfa(self):
        payload = {"scenario": "mfa_all_privileged"}
        data = self._post("/api/simulation/run", payload)
        self.assertEqual(data["before_eal"], 3420000.0)
        self.assertEqual(data["after_eal"], 2620000.0)
        self.assertEqual(data["risk_reduction"], 800000.0)

    def test_live_post_simulation_run_delay(self):
        payload = {"scenario": "delay_remediation_30_days"}
        data = self._post("/api/simulation/run", payload)
        self.assertEqual(data["before_eal"], 3420000.0)
        self.assertEqual(data["after_eal"], 4140000.0)
        self.assertEqual(data["risk_reduction"], -720000.0)


if __name__ == "__main__":
    unittest.main()
