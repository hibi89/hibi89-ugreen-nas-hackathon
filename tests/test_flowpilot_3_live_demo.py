"""Synthetic-only live demo tests on loopback socket; no external network."""
import csv
import json
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from hashlib import sha256
from pathlib import Path
from flowpilot_3_live_demo import DemoController, create_server


class DemoControllerTests(unittest.TestCase):
    def setUp(self):
        self.demo = DemoController()
        self.addCleanup(self.demo.close)

    def test_preview_is_readonly_and_reject(self):
        original = sha256((self.demo.root / 'jan.csv').read_bytes()).hexdigest()
        self.assertEqual(self.demo.view()['status'], 'WAITING_USER')
        pre = self.demo.act('preview')
        self.assertEqual(pre['status'], 'WAITING_EXECUTION_APPROVAL')
        self.assertFalse((self.demo.root / 'summary.csv').exists())
        self.assertEqual(pre['la_compatibility']['status'], 'BLOCKED_MISSING_CAPABILITIES')
        rej = self.demo.act('reject')
        self.assertEqual(rej['status'], 'DECLINED')
        self.assertFalse((self.demo.root / 'summary.csv').exists())
        self.assertEqual(original, sha256((self.demo.root / 'jan.csv').read_bytes()).hexdigest())
        with self.assertRaises(ValueError):
            self.demo.act('approve')

    def test_approved_workflow_exact_output_and_audit(self):
        self.demo.act('preview')
        result = self.demo.act('approve')
        self.assertEqual(result['status'], 'LOCAL_REPORT_CREATED_NOT_NAS')
        self.assertEqual(result['audit']['count'], 1)
        with (self.demo.root / 'summary.csv').open(encoding='utf-8', newline='') as f:
            self.assertEqual(list(csv.reader(f)), [['customer','total_revenue'],['alice','5.00'],['bob','6.00']])
        with self.assertRaises(ValueError):
            self.demo.act('approve')

    def test_invalid_action_refused(self):
        with self.assertRaises(ValueError):
            self.demo.act('delete')


class DemoHTTPTests(unittest.TestCase):
    def setUp(self):
        self.demo = DemoController()
        self.server = create_server(self.demo)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.demo.close()

    def request(self, path, *, token=True, origin=None):
        headers={'Content-Type': 'application/json'}
        if token: headers['X-Flowpilot-Token'] = self.demo.token
        if origin: headers['Origin']=origin
        return urlopen(Request(self.url + path, method='POST', data=b'{}', headers=headers), timeout=3)

    def test_get_status_and_ui(self):
        with urlopen(self.url + '/', timeout=3) as r:
            html=r.read().decode()
            self.assertIn('NAS UNVERIFIED',html)
            self.assertIn('Approve &amp; run',html)
        with urlopen(self.url + '/api/state', timeout=3) as r:
            self.assertEqual(json.load(r)['status'], 'WAITING_USER')

    def test_cross_site_request_refused(self):
        with self.assertRaises(HTTPError) as c:
            self.request('/api/approve',token=False)
        self.assertEqual(c.exception.code,403)
        with self.assertRaises(HTTPError) as c:
            self.request('/api/preview',origin='https://evil.example')
        self.assertEqual(c.exception.code,403)

    def test_http_end_to_end(self):
        with self.request('/api/preview') as r:
            self.assertEqual(json.load(r)['status'], 'WAITING_EXECUTION_APPROVAL')
        with self.request('/api/approve') as r:
            data=json.load(r)
            self.assertEqual(data['status'],'LOCAL_REPORT_CREATED_NOT_NAS')
            self.assertFalse(data['nas_verified'])
        with self.assertRaises(HTTPError) as c:
            self.request('/api/approve')
        self.assertEqual(c.exception.code,409)


if __name__ == '__main__':
    unittest.main()
