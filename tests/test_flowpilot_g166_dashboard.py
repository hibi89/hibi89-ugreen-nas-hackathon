"""G166 static local dashboard, CSP/security and browser-client/HTTP regression.

The Node harness simulates DOM events against a REAL temporary Python HTTP
server and SQLite database; it is NOT a Chromium/Firefox visual assertion.
No UGREEN trial, NAS, vendor SDK, private files, or external request is made.
"""
from __future__ import annotations

import http.client
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from flowpilot_local_backend import Backend, create_server

TOKEN = "g166" * 12
ASSETS = {
    "/dashboard": ("flowpilot_g166_dashboard.html", "text/html"),
    "/dashboard.css": ("flowpilot_g166_dashboard.css", "text/css"),
    "/dashboard.js": ("flowpilot_g166_dashboard.js", "text/javascript"),
}


class G166LocalDashboardTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "non-nas-disposable"
        self.root.mkdir()
        (self.root / "README.md").write_text("synthetic", encoding="utf-8")
        self.db = Path(temp.name) / "g166-new.sqlite"
        self.backend = Backend(self.db, create=True, metadata_root=self.root)
        self.server = create_server(self.backend, TOKEN, port=0)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.base = f"127.0.0.1:{self.server.server_port}"

    def get(self, path, *, token=None, host=None, origin=None):
        headers = {"Host": host or self.base}
        if token:
            headers["Authorization"] = "Bearer " + token
        if origin:
            headers["Origin"] = origin
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            conn.request("GET", path, headers=headers)
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_local_assets_available_without_token_but_api_denied(self):
        for path, (filename, expected_type) in ASSETS.items():
            with self.subTest(path=path):
                status, headers, content = self.get(path)
                self.assertEqual(status, 200)
                self.assertEqual(content, (TOOLS / filename).read_bytes())
                self.assertTrue(headers["Content-Type"].startswith(expected_type))
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(headers["X-Frame-Options"], "DENY")
                self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])
                self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
                self.assertNotIn(TOKEN.encode(), content)
        self.assertEqual(self.get("/v1/health")[0], 403)
        self.assertEqual(self.get("/v1/health", token=TOKEN)[0], 200)

    def test_host_origin_boundaries_applied_to_static_and_api(self):
        for path in ASSETS:
            with self.subTest(path=path):
                self.assertEqual(self.get(path, host="evil.example")[0], 403)
                self.assertEqual(self.get(path, origin="https://evil.example")[0], 403)
        self.assertEqual(self.get("/dashboard?token=private")[0], 403)
        self.assertEqual(self.get("/dashboard.js/../dashboard")[0], 403)
        self.assertEqual(self.get("/dashboard", origin=f"http://{self.base}")[0], 200)
        self.assertEqual(self.get("/v1/health", token=TOKEN,
                                  origin="https://evil.example")[0], 403)

    def test_no_inline_credentials_or_cross_origin_scripts(self):
        html = (TOOLS / ASSETS["/dashboard"][0]).read_text(encoding="utf-8")
        js = (TOOLS / ASSETS["/dashboard.js"][0]).read_text(encoding="utf-8")
        self.assertIn('src="/dashboard.js"', html)
        self.assertIn('href="/dashboard.css"', html)
        self.assertIn('type="password"', html)
        self.assertNotIn("<script>", html)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("sessionStorage", js)
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("credentials: \"include\"", js)
        self.assertIn('credentials: "omit"', js)
        self.assertIn("crypto.subtle.digest", js)
        self.assertIn("APPROVE_LOCAL_METADATA_READ_ONLY", js)
        self.assertIn("APPROVE_SYNTHETIC_ONLY", js)
        self.assertIn('id="refresh"', html)
        self.assertIn("UNKNOWN_REQUIRES_READBACK", js)
        self.assertIn('json("/v1/workflows/" + id)', js)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable, JS runtime NOT_VERIFIED")
    def test_js_syntax_and_simulated_dom_over_real_http(self):
        checks = [
            ["node", "--check", str(TOOLS / "flowpilot_g166_dashboard.js")],
            ["node", "--check",
             str(Path(__file__).resolve().parent / "g166_browser_client_smoke.cjs")],
            ["node", str(Path(__file__).resolve().parent / "g166_browser_client_smoke.cjs"),
             "http://" + self.base, TOKEN]
        ]
        for command in checks:
            with self.subTest(command=command[1]):
                run = subprocess.run(command, capture_output=True, text=True,
                                     timeout=35, check=False)
                self.assertEqual(run.returncode, 0,
                                 f"{command[1]}: {run.stdout[-1500:]}\n{run.stderr[-2000:]}")
                if command[1].endswith(".cjs"):
                    self.assertIn("G166_NODE_DOM_HTTP_SMOKE_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
