"""Guided synthetic CSV selection, approval, and HTTP security tests."""
import csv
from io import StringIO
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from flowpilot_3_live_demo import DemoController, create_server


class GuidedControllerTests(unittest.TestCase):
    def setUp(self):
        self.demo = DemoController()
        self.addCleanup(self.demo.close)

    def test_selected_single_file_and_new_output(self):
        state = self.demo.configure({"goal": "고객별 매출 보고서 만들어줘",
                                     "sources": ["jan.csv"], "output": "monthly-summary.csv"})
        self.assertEqual(state["status"], "WAITING_EXECUTION_APPROVAL")
        self.assertEqual(len([n for n in state["workflow_graph"]["nodes"]
                              if n["type"] == "csv_read"]), 1)
        self.assertFalse((self.demo.root / "monthly-summary.csv").exists())
        approved = self.demo.act("approve")
        self.assertEqual(approved["status"], "LOCAL_REPORT_CREATED_NOT_NAS")
        self.assertEqual(list(csv.reader(StringIO(self.demo.report_csv().decode("utf-8")))),
                         [["customer", "total_revenue"], ["alice", "1.25"], ["bob", "2.00"]])
        self.assertFalse((self.demo.root / "summary.csv").exists())

    def test_rejection_and_reconfiguration(self):
        self.demo.configure({"goal": "고객별 매출 보고서 만들어줘", "sources": ["jan.csv"],
                             "output": "summary.csv"})
        self.demo.act("reject")
        with self.assertRaises(ValueError):
            self.demo.act("approve")
        self.demo.configure({"goal": "create customer revenue summary", "sources": ["feb.csv"],
                             "output": "summary.csv"})
        self.assertEqual(self.demo.act("approve")["status"], "LOCAL_REPORT_CREATED_NOT_NAS")
        self.assertEqual(list(csv.reader(StringIO(self.demo.report_csv().decode("utf-8"))))[1],
                         ["alice", "3.75"])

    def test_invalid_selection_cannot_replace_approved_plan(self):
        self.demo.configure({"goal": "고객별 매출 보고서 만들어줘", "sources": ["jan.csv"],
                             "output": "summary.csv"})
        for bad in (
            {"goal": "delete everything", "sources": ["jan.csv"], "output": "summary.csv"},
            {"goal": "고객별 매출 보고서 만들어줘", "sources": ["../secrets.csv"], "output": "summary.csv"},
            {"goal": "고객별 매출 보고서 만들어줘", "sources": ["jan.csv"], "output": "../../leak.csv"},
            {"goal": "고객별 매출 보고서 만들어줘", "sources": [], "output": "summary.csv"},
            {"goal": "고객별 매출 보고서 만들어줘", "sources": ["jan.csv", "jan.csv"], "output": "summary.csv"},
            {"goal": "고객별 매출 보고서 만들어줘", "sources": ["jan.csv"], "output": "summary.csv", "root": "/etc"},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.demo.configure(bad)
        self.assertEqual(self.demo.act("approve")["status"], "LOCAL_REPORT_CREATED_NOT_NAS")

    def test_cannot_reconfigure_after_execution(self):
        self.demo.act("preview")
        self.demo.act("approve")
        with self.assertRaises(ValueError):
            self.demo.configure({"goal": "고객별 매출 보고서 만들어줘", "sources": ["jan.csv"],
                                 "output": "summary.csv"})


class GuidedHTTPTests(unittest.TestCase):
    def setUp(self):
        self.demo = DemoController()
        self.server = create_server(self.demo)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.addCleanup(self.clean)

    def clean(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.demo.close()

    def request(self, payload, *, token=True, origin=None):
        body=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        headers={"Content-Type":"application/json"}
        if token:
            headers["X-Flowpilot-Token"]=self.demo.token
        if origin:
            headers["Origin"]=origin
        return urlopen(Request(self.url+'/api/configure',headers=headers,
                               method='POST',data=body),timeout=3)

    def test_http_configure_and_approve(self):
        with self.request({"goal":"고객별 매출 보고서 만들어줘","sources":["feb.csv"],"output":"monthly-summary.csv"}) as response:
            self.assertEqual(json.load(response)["status"],"WAITING_EXECUTION_APPROVAL")
        approval=Request(self.url+'/api/approve',data=b'{}',method='POST',
                         headers={'Content-Type':'application/json','X-Flowpilot-Token':self.demo.token})
        with urlopen(approval,timeout=3) as response:
            self.assertEqual(json.load(response)['status'],'LOCAL_REPORT_CREATED_NOT_NAS')
        self.assertIn(b'3.75',self.demo.report_csv())

    def test_http_no_token_or_bad_origin_blocked(self):
        payload={"goal":"고객별 매출 보고서 만들어줘","sources":["jan.csv"],"output":"summary.csv"}
        with self.assertRaises(HTTPError) as err:
            self.request(payload, token=False)
        self.assertEqual(err.exception.code,403)
        with self.assertRaises(HTTPError) as err:
            self.request(payload, origin='https://evil.example')
        self.assertEqual(err.exception.code,403)
        self.assertEqual(self.demo.view()['status'],'WAITING_USER')


if __name__ == '__main__':
    unittest.main()
