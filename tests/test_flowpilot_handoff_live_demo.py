"""End-to-end synthetic handoff demo UI: no actual NAS or private user data."""
from __future__ import annotations

import copy
import json
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_handoff_live_demo import HandoffDemo, create_server, fixture


class HandoffControllerTests(unittest.TestCase):
    def setUp(self):
        self.demo = HandoffDemo()

    def test_preview_never_grants_metadata_approval(self):
        view = self.demo.action("preview", {"scenario": "handoff"})
        self.assertEqual(view["phase"], "WAITING_METADATA_APPROVAL")
        self.assertEqual(view["report"]["file_stage"]["item_count"], 0)
        self.assertEqual(view["report"]["file_stage"]["status"], "WAITING_APPROVAL")
        self.assertFalse(view["actual_uliya_or_nas_invoked"])
        self.assertEqual(view["release_gate"], "HOLD")

    def test_separate_metadata_approval_required(self):
        self.demo.action("preview", {"scenario": "handoff"})
        for data in ({"ack_unknown_processing": False}, {"ack_unknown_processing": "true"},
                     {}, {"ack_unknown_processing": True, "extra": "secret"}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.demo.action("approve-metadata", data)
        view = self.demo.action("approve-metadata", {"ack_unknown_processing": True})
        self.assertEqual(view["phase"], "REVIEW_AVAILABLE")
        self.assertEqual(view["report"]["file_stage"]["counts"]["PRESENT"], 2)
        self.assertFalse(view["report"]["real_nas_verified"])

    def test_missing_and_conflicting_versions_never_ready(self):
        for scenario, expected in (("missing", "MISSING"), ("versions", "VERSION_REVIEW")):
            with self.subTest(scenario=scenario):
                self.demo.action("preview", {"scenario": scenario})
                view = self.demo.action("approve-metadata", {"ack_unknown_processing": True})
                self.assertEqual(view["report"]["file_stage"]["counts"][expected], 1)
                self.assertFalse(view["report"]["overall_ready_certified"])
                self.assertEqual(view["report"]["release_gate"], "HOLD")
                if scenario == "missing":
                    self.assertEqual(view["report"]["status"],
                                     "SYNTHETIC_BLOCKED_NEEDS_OWNER_REVIEW")

    def test_document_previews_without_content_access(self):
        self.demo.action("preview", {"scenario": "document"})
        self.demo.action("approve-metadata", {"ack_unknown_processing": True})
        preview = self.demo.action("preview-document",
                                   {"question": "Summarize delivery risks?", "select_document": True})
        self.assertEqual(preview["phase"], "WAITING_DOCUMENT_APPROVAL")
        self.assertEqual(preview["report"]["document_stage"]["status"],
                         "WAITING_SEPARATE_DOCUMENT_APPROVAL")
        self.assertEqual(preview["report"]["document_stage"]["claimed_answer_count"], 0)
        self.assertIsInstance(preview["consent_nonce"], str)
        self.assertFalse(preview["report"]["document_agent_live_verified"])

    def test_document_requires_fresh_consent_nonce(self):
        self.demo.action("preview", {"scenario": "document"})
        self.demo.action("approve-metadata", {"ack_unknown_processing": True})
        preview = self.demo.action("preview-document",
                                   {"question": "Summarize delivery risks?", "select_document": True})
        nonce = preview["consent_nonce"]
        for data in ({"approve_content": True, "consent_nonce": "wrong"},
                     {"approve_content": "true", "consent_nonce": nonce},
                     {"approve_content": False, "consent_nonce": nonce}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.demo.action("approve-document", data)
        state = self.demo.action("approve-document",
                                 {"approve_content": True, "consent_nonce": nonce})
        self.assertEqual(state["phase"], "REVIEW_AVAILABLE")
        self.assertEqual(state["report"]["document_stage"]["claimed_answer_count"], 1)
        self.assertEqual(state["report"]["document_stage"]["status"],
                         "SYNTHETIC_ANSWER_CLAIMS_NEED_REVIEW")
        self.assertFalse(state["report"]["real_nas_verified"])
        with self.assertRaises(ValueError):
            self.demo.action("approve-document",
                             {"approve_content": True, "consent_nonce": nonce})

    def test_preview_change_invalidates_previous_document_consent(self):
        self.demo.action("preview", {"scenario": "document"})
        self.demo.action("approve-metadata", {"ack_unknown_processing": True})
        old = self.demo.action("preview-document",
                               {"question": "Summarize delivery risks?", "select_document": True})
        new = self.demo.action("preview-document",
                               {"question": "Summarize version changes?", "select_document": True})
        self.assertNotEqual(old["consent_nonce"], new["consent_nonce"])
        with self.assertRaises(ValueError):
            self.demo.action("approve-document",
                             {"approve_content": True, "consent_nonce": old["consent_nonce"]})
        self.demo.action("preview", {"scenario": "missing"})
        self.assertIsNone(self.demo.snapshot()["consent_nonce"])

    def test_bad_goals_and_unexpected_payloads_refused(self):
        for scenario in ("shell_exec", "../private", 0, None, {}, []):
            with self.subTest(scenario=scenario), self.assertRaises(ValueError):
                fixture(scenario)
        with self.assertRaises(ValueError):
            self.demo.action("preview", {"scenario": "handoff", "root": "/etc"})
        with self.assertRaises(ValueError):
            self.demo.action("delete-files", {})

    def test_document_answer_not_exposed_in_any_view(self):
        self.demo.action("preview", {"scenario": "document"})
        self.demo.action("approve-metadata", {"ack_unknown_processing": True})
        preview = self.demo.action("preview-document",
                                   {"question": "Summarize delivery risks?", "select_document": True})
        end = self.demo.action("approve-document",
                               {"approve_content": True,
                                "consent_nonce": preview["consent_nonce"]})
        serialized = json.dumps(end)
        for hidden in ("Synthetic fixture answer only", "synthetic://deliverable-2",
                       "/synthetic/flowpilot-demo", "Summarize delivery risks?",
                       "release/output.pdf"):
            self.assertNotIn(hidden, serialized)
        html = self.demo.current_dashboard()
        self.assertIn("Owner Review", html)
        self.assertNotIn("synthetic://deliverable-2", html)
        self.assertNotIn("/synthetic/flowpilot-demo", html)
        self.assertNotIn("Synthetic fixture answer only", html)

    def test_out_of_order_actions_refused(self):
        with self.assertRaises(ValueError):
            self.demo.action("approve-metadata", {"ack_unknown_processing": True})
        with self.assertRaises(ValueError):
            self.demo.action("preview-document",
                             {"question": "Summarize?", "select_document": True})
        with self.assertRaises(ValueError):
            self.demo.current_dashboard()
        self.demo.action("preview", {"scenario": "handoff"})
        with self.assertRaises(ValueError):
            self.demo.action("preview-document",
                             {"question": "Summarize?", "select_document": True})


class HandoffHTTPTests(unittest.TestCase):
    def setUp(self):
        self.demo = HandoffDemo()
        self.server = create_server(self.demo, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def post(self, action: str, data: dict, *, authenticated=True, origin=None):
        raw = json.dumps(data).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if authenticated:
            headers["X-Flowpilot-Token"] = self.demo.token
        if origin:
            headers["Origin"] = origin
        return urlopen(Request(self.url + "/api/" + action,
                               method="POST", data=raw, headers=headers), timeout=3)

    def test_http_page_and_status(self):
        with urlopen(self.url + "/", timeout=3) as r:
            text = r.read().decode("utf-8")
            self.assertIn("Round 1", text.lower().replace("round 1", "Round 1"))
            self.assertIn("NAS FlowPilot 3.0", text)
        with urlopen(self.url + "/api/state", timeout=3) as r:
            data = json.load(r)
            self.assertEqual(data["phase"], "WAITING_PREVIEW")

    def test_http_full_document_approval_flow(self):
        with self.post("preview", {"scenario": "document"}) as r:
            self.assertEqual(json.load(r)["phase"], "WAITING_METADATA_APPROVAL")
        with self.post("approve-metadata", {"ack_unknown_processing": True}) as r:
            self.assertEqual(json.load(r)["phase"], "WAITING_DOCUMENT_SELECTION")
        with self.post("preview-document",
                       {"question": "Summarize delivery risks?", "select_document": True}) as r:
            nonce = json.load(r)["consent_nonce"]
        with self.post("approve-document",
                       {"consent_nonce": nonce, "approve_content": True}) as r:
            data = json.load(r)
            self.assertEqual(data["phase"], "REVIEW_AVAILABLE")
            self.assertEqual(data["report"]["document_stage"]["claimed_answer_count"], 1)
        with urlopen(self.url + "/api/dashboard", timeout=3) as r:
            html = r.read().decode("utf-8")
            self.assertIn("Owner Review", html)
            self.assertNotIn("synthetic://deliverable-2", html)

    def test_csrf_and_cross_origin_are_refused(self):
        with self.assertRaises(HTTPError) as e:
            self.post("preview", {"scenario": "handoff"}, authenticated=False)
        self.assertEqual(e.exception.code, 403)
        with self.assertRaises(HTTPError) as e:
            self.post("preview", {"scenario": "handoff"},
                      origin="https://untrusted.example")
        self.assertEqual(e.exception.code, 403)
        self.assertEqual(self.demo.snapshot()["phase"], "WAITING_PREVIEW")

    def test_unknown_http_action_refused(self):
        with self.assertRaises(HTTPError) as e:
            self.post("upload", {})
        self.assertEqual(e.exception.code, 404)
        with self.assertRaises(HTTPError) as e:
            urlopen(self.url + "/api/dashboard", timeout=3)
        self.assertEqual(e.exception.code, 409)


if __name__ == "__main__":
    unittest.main()
