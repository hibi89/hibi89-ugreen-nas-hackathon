"""Verify the browser demo does not serve files that differ from audited bytes."""
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from flowpilot_3_live_demo import DemoController, create_server


class ReceiptDownloadTests(unittest.TestCase):
    def setUp(self):
        self.demo = DemoController()
        self.addCleanup(self.demo.close)

    def test_audited_report_can_download(self):
        self.demo.act('preview')
        state = self.demo.act('approve')
        record = state['execution']['result']
        self.assertEqual(len(record['report_sha256']), 64)
        self.assertEqual(len(record['node_trace']), 5)
        self.assertIn(b'alice,5.00', self.demo.report_csv())

    def test_tampered_output_is_refused(self):
        self.demo.act('preview')
        self.demo.act('approve')
        report = self.demo.root / 'summary.csv'
        report.write_text('customer,total_revenue\nalice,99999\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'digest differs'):
            self.demo.report_csv()

    def test_tampered_output_refused_by_http(self):
        self.demo.act('preview')
        self.demo.act('approve')
        report = self.demo.root / 'summary.csv'
        report.write_text('tampered', encoding='utf-8')
        server = create_server(self.demo)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(f'http://127.0.0.1:{server.server_port}/api/report',
                              headers={'X-Flowpilot-Token': self.demo.token})
            with self.assertRaises(HTTPError) as ctx:
                urlopen(request, timeout=3)
            self.assertEqual(ctx.exception.code, 409)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
