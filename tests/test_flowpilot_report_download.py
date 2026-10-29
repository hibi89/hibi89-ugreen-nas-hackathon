"""Local-only approved CSV delivery tests. No NAS or user files."""
import csv
import threading
import unittest
from io import StringIO
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from flowpilot_3_live_demo import DemoController, create_server


class ReportDownloadTests(unittest.TestCase):
    def setUp(self):
        self.demo = DemoController()
        self.server = create_server(self.demo)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/api/report"
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.demo.close()

    def _get(self, *, token=True):
        headers = {"X-Flowpilot-Token": self.demo.token} if token else {}
        return urlopen(Request(self.url, headers=headers), timeout=3)

    def test_unapproved_report_is_absent(self):
        with self.assertRaises(ValueError):
            self.demo.report_csv()
        with self.assertRaises(HTTPError) as ctx:
            self._get()
        self.assertEqual(ctx.exception.code, 409)

    def test_report_requires_session_token(self):
        self.demo.act("preview")
        self.demo.act("approve")
        with self.assertRaises(HTTPError) as ctx:
            self._get(token=False)
        self.assertEqual(ctx.exception.code, 403)

    def test_download_matches_approved_report(self):
        self.demo.act("preview")
        self.demo.act("approve")
        with self._get() as response:
            self.assertEqual(response.headers.get_content_type(), "text/csv")
            received = response.read()
        rows = list(csv.reader(StringIO(received.decode("utf-8"))))
        self.assertEqual(rows, [["customer", "total_revenue"], ["alice", "5.00"], ["bob", "6.00"]])
        self.assertEqual(received, self.demo.report_csv())

    def test_rejected_preview_cannot_download(self):
        self.demo.act("preview")
        self.demo.act("reject")
        with self.assertRaises(HTTPError) as ctx:
            self._get()
        self.assertEqual(ctx.exception.code, 409)


if __name__ == "__main__":
    unittest.main()
