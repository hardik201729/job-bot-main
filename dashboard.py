"""
JobBot dashboard - replaces Google Sheets.

Run:   venv/bin/python dashboard.py
Opens: http://127.0.0.1:8050  (analytics + every table the bot writes)

It only reads data/jobbot.db, so it is safe to keep open while the bot runs;
the page refreshes itself every 30 seconds.
"""

import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from local_store import DB_PATH, export_all

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(BASE_DIR, "dashboard", "index.html")
PORT = int(os.environ.get("DASHBOARD_PORT", "8050"))


def _settings():
    try:
        import config
        return {
            "min_match_score": config.MIN_MATCH_SCORE,
            "top_jobs_to_apply": config.TOP_JOBS_TO_APPLY,
            "hr_per_job": config.EMAILS_PER_COMPANY,
            "referrals_per_job": config.REFERRALS_PER_COMPANY,
            "apollo_total_credits": getattr(config, "APOLLO_TOTAL_CREDITS", None),
            "apollo_max_per_run": getattr(config, "MAX_APOLLO_CREDITS_PER_RUN", None),
        }
    except Exception:
        return {}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(PAGE, "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/data":
            data = export_all() if os.path.exists(DB_PATH) else {}
            body = json.dumps({"sheets": data, "settings": _settings()}).encode()
            self._send(200, body, "application/json")
        else:
            self._send(404, b"Not found", "text/plain")

    def log_message(self, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"JobBot dashboard running at {url}  (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
