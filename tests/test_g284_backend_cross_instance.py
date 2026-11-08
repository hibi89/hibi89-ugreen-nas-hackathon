"""G284: concurrent Backend instances on one local SQLite DB must not replay stages.

Only synthetic disposable local fixtures; no NAS, vendor or owner data.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_local_backend as api


class G284MultiInstanceAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "private-synthetic.sqlite"
        self.first = api.Backend(self.path, create=True)
        self.second = api.Backend(self.path)

    @staticmethod
    def parallel(first, second):
        """Start both independent requests at the same barrier, return results."""
        gate = threading.Barrier(3, timeout=10)
        def call(fn):
            gate.wait()
            return fn()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(call, first)
            b = pool.submit(call, second)
            gate.wait()
            return a.result(timeout=20), b.result(timeout=20)

    def test_simultaneous_council_is_single_committed_transition(self):
        item = self.first.create("check required files", "req_g284council123")
        wf = item["workflow_id"]
        original = api.run_council
        calls = []
        count_lock = threading.Lock()
        def deliberate_overlap(goal):
            with count_lock:
                calls.append(goal)
            time.sleep(0.08)
            return original(goal)
        with patch.object(api, "run_council", side_effect=deliberate_overlap):
            two = self.parallel(lambda: self.first.test(wf),
                                lambda: self.second.test(wf))
        self.assertEqual([x["status"] for x in two], ["TESTED", "TESTED"])
        self.assertEqual(len(calls), 1, "synthetic QA must not run twice")
        self.assertEqual(api.Backend(self.path).verified_get(wf)["event_count"], 2)

    def test_two_approvals_add_exactly_one_consent_event(self):
        item = self.first.create("check required files", "req_g284approval12")
        wf = item["workflow_id"]
        self.first.test(wf)
        results = self.parallel(
            lambda: self.first.approve(wf, item["plan_sha256"], "APPROVE_SYNTHETIC_ONLY"),
            lambda: self.second.approve(wf, item["plan_sha256"], "APPROVE_SYNTHETIC_ONLY"))
        self.assertEqual([x["status"] for x in results],
                         ["APPROVED_SYNTHETIC", "APPROVED_SYNTHETIC"])
        state = api.Backend(self.path).verified_get(wf)
        self.assertEqual(state["event_count"], 3)
        self.assertEqual(state["status"], "APPROVED_SYNTHETIC")

    def test_parallel_synthetic_run_never_reserves_twice(self):
        item = self.first.create("check required files", "req_g284runonce12")
        wf = item["workflow_id"]
        self.first.test(wf)
        self.first.approve(wf, item["plan_sha256"], "APPROVE_SYNTHETIC_ONLY")
        original = api.run_once
        executed = []
        lock = threading.Lock()
        def delayed_once(*args, **kwargs):
            with lock:
                executed.append(True)
            time.sleep(0.10)
            return original(*args, **kwargs)
        def run(instance):
            try:
                return instance.run(wf)["status"]
            except api.BackendRefused as exc:
                return exc.code
        with patch.object(api, "run_once", side_effect=delayed_once):
            results = self.parallel(lambda: run(self.first),
                                    lambda: run(self.second))
        self.assertEqual(len(executed), 1, "reservation must precede concurrent runner")
        self.assertIn("COMPLETE_LOCAL_SYNTHETIC", results)
        self.assertTrue(set(results) <= {"COMPLETE_LOCAL_SYNTHETIC", "RUN_STATE_CONFLICT"})
        again = api.Backend(self.path)
        self.assertEqual(again.verified_get(wf)["event_count"], 5)
        self.assertEqual(again.evidence(wf)["status"],
                         "LOCAL_SYNTHETIC_EVIDENCE_VERIFIED_NOT_NAS")
        self.assertFalse(again.verified_get(wf)["nas_verified"])


if __name__ == "__main__":
    unittest.main()
