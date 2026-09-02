"""
P4 HTTP Server for CYBERVAL.
Runs a production-ready HTTP/REST server serving:
- POST /api/ai/query
- POST /api/ai/recommend
- POST /api/simulation/run
- GET /health
- GET /api/docs
"""

import sys
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Tuple
from .api import P4APIService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CYBERVAL_P4")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP Server for non-blocking concurrent API requests."""
    daemon_threads = True
    allow_reuse_address = True


class P4HTTPRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler routing incoming calls to P4APIService.
    """

    api_service = P4APIService()

    def _set_cors_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(204)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path == "/health" or path == "":
            res = self.api_service.handle_health()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
        elif path == "/api/docs":
            res = self.api_service.handle_docs()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            err = {"error": "Not Found", "message": f"Cannot GET {self.path}"}
            self.wfile.write(json.dumps(err).encode("utf-8"))

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_length > 0:
            try:
                raw_data = self.rfile.read(content_length).decode("utf-8")
                body = json.loads(raw_data) if raw_data.strip() else {}
            except json.JSONDecodeError:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Bad Request", "message": "Invalid JSON format"}).encode("utf-8"))
                return

        if path == "/api/ai/query":
            res = self.api_service.handle_ai_query(body)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))

        elif path == "/api/ai/recommend":
            res = self.api_service.handle_ai_recommend(body)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))

        elif path == "/api/simulation/run":
            res = self.api_service.handle_simulation_run(body)
            status = 400 if "error" in res else 200
            self._set_cors_headers(status)
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))

        else:
            self._set_cors_headers(404)
            err = {"error": "Not Found", "message": f"Cannot POST {self.path}"}
            self.wfile.write(json.dumps(err).encode("utf-8"))

    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


def run_server(host: str = "0.0.0.0", port: int = 8080):
    server = ThreadedHTTPServer((host, port), P4HTTPRequestHandler)
    logger.info(f"CYBERVAL P4 AI Decision Support Server running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port=port)
