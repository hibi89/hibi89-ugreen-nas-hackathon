"""G74: common CLI runs genuine owner-specified LOCAL metadata under consent.

No file contents, registered Uliya Expert, NAS, HAE, LA, DBVORA or SOVIA.
These fixtures are disposable local folders, not simulated network shares.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from flowpilot_csv_e2e import main, run_session
from flowpilot_csv_report import ReportRefused


class G74RealLocalMetadataCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="flowpilot-g74-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "README.md").write_bytes(b"synthetic local input: unchanged")
        (self.root / "release").mkdir()
        (self.root / "release" / "final.pdf").write_bytes(b"v1")
        (self.root / "release" / "final_v2.pdf").write_bytes(b"v2")
        self.args = dict(
            goal="인계 확인하고 파일 누락 확인하고 버전 비교해줘",
            backend="projectready-local-metadata", root=self.root,
            required=["README.md", "release/final.pdf"],
            candidates={"release/final.pdf": ["release/final_v2.pdf"]},
        )

    def test_g74_intake_missing_slots_without_owner_access(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("owner root accessed")):
            outcome = run_session("필수 파일 확인",
                                  backend="projectready-local-metadata")
        self.assertEqual(outcome["status"], "WAITING_USER")
        self.assertEqual(outcome["planned_steps"], 1)
        self.assertEqual(outcome["executed_steps"], 0)
        self.assertFalse(outcome["executed"])

    def test_complete_preview_never_touches_owner_folder(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("owner root accessed")):
            outcome = run_session(**self.args)
        self.assertEqual(outcome["status"], "WAITING_APPROVAL")
        self.assertEqual(outcome["planned_steps"], 3)
        self.assertEqual(outcome["executed_steps"], 0)
        self.assertFalse(outcome["executed"])
        self.assertFalse(outcome["owner_folder_metadata_accessed"])

    def test_csv_approval_is_not_metadata_approval(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("owner root accessed")):
            result = run_session(**self.args, approval="APPROVE_EXECUTION")
        self.assertEqual(result["status"], "DECLINED")
        self.assertFalse(result["executed"])

    def test_la_approval_is_not_metadata_approval(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("owner root accessed")):
            result = run_session(**self.args, approval="APPROVE_SYNTHETIC_SQLITE_IMPORT")
        self.assertEqual(result["status"], "DECLINED")
        self.assertFalse(result["executed"])

    def test_real_disposable_local_three_stage_execution_and_privacy(self):
        before = (self.root / "README.md").read_bytes()
        result = run_session(**self.args, approval="APPROVE_LOCAL_METADATA")
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["executed_steps"], 3)
        self.assertTrue(result["executed"])
        self.assertEqual(result["finding_counts"]["VERSION_REVIEW"], 1)
        self.assertTrue(result["review_required"])
        self.assertFalse(result["file_contents_opened"])
        self.assertFalse(result["actual_uliya_nas_integrated"])
        self.assertFalse(result["actual_la_integrated"])
        self.assertEqual(before, (self.root / "README.md").read_bytes())
        text = json.dumps(result, ensure_ascii=False)
        for forbidden in (str(self.root), "README.md", "release/final_v2.pdf",
                          "synthetic local input"):
            self.assertNotIn(forbidden, text)

    def test_missing_file_returns_blocked_and_only_first_stage_runs(self):
        params = dict(self.args, required=["missing.md"])
        params["candidates"] = {"missing.md": ["release/final_v2.pdf"]}
        result = run_session(**params, approval="APPROVE_LOCAL_METADATA")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["executed_steps"], 1)
        self.assertTrue(result["executed"])
        self.assertFalse(result["nas_verified"])

    def test_traversal_rejected_even_with_metadata_consent(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("owner root accessed")):
            with self.assertRaises(ValueError):
                run_session(goal="파일 확인", backend="projectready-local-metadata",
                            root=self.root, required=["../secret.env"],
                            approval="APPROVE_LOCAL_METADATA")

    def test_unrecognized_mutation_intent_rejected_before_root_access(self):
        with patch("flowpilot_owner_local_audit._valid_root",
                   side_effect=AssertionError("owner root accessed")):
            with self.assertRaises(ValueError):
                run_session(goal="파일 삭제해줘", backend="projectready-local-metadata",
                            root=self.root, required=["README.md"],
                            approval="APPROVE_LOCAL_METADATA")

    def test_metadata_mode_rejects_csv_write_and_audit_paths(self):
        extras = dict(sources=["sales.csv"], output="report.csv", group="x",
                      amount="y", audit_db=self.root / "audit.sqlite")
        for name, value in extras.items():
            with self.subTest(name=name):
                with patch("flowpilot_owner_local_audit._valid_root",
                           side_effect=AssertionError("owner root accessed")):
                    with self.assertRaises(ReportRefused):
                        run_session(**self.args, **{name: value},
                                    approval="APPROVE_LOCAL_METADATA")

    def test_default_csv_and_la_backends_reject_metadata_checklists(self):
        for backend in ("local-csv-report", "la-synthetic-import"):
            with self.subTest(backend=backend), self.assertRaises(ReportRefused):
                run_session("파일 확인", backend=backend,
                            required=["README.md"])

    def test_real_cli_preview_then_separate_approved_execution(self):
        cmd = [sys.executable, str(TOOLS / "flowpilot_csv_e2e.py"),
               "--backend", "projectready-local-metadata", "--goal",
               "파일 확인", "--root", str(self.root), "--required", "README.md"]
        preview = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        before = json.loads(preview.stdout)
        self.assertEqual(before["status"], "WAITING_APPROVAL")
        self.assertFalse(before["executed"])
        approved = subprocess.run(cmd + ["--approval", "APPROVE_LOCAL_METADATA"],
                                  capture_output=True, text=True, timeout=15)
        self.assertEqual(approved.returncode, 0, approved.stderr)
        after = json.loads(approved.stdout)
        self.assertEqual(after["status"], "NEEDS_REVIEW")
        self.assertTrue(after["executed"])
        self.assertEqual(after["finding_counts"]["PRESENT"], 1)
        self.assertNotIn(str(self.root), approved.stdout)

    def test_cli_blocked_exit_code_and_no_secrets_in_output(self):
        cmd = [sys.executable, str(TOOLS / "flowpilot_csv_e2e.py"),
               "--backend", "projectready-local-metadata", "--goal",
               "파일 확인", "--root", str(self.root), "--required", "missing.md",
               "--approval", "APPROVE_LOCAL_METADATA"]
        outcome = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(outcome.returncode, 1, outcome.stderr)
        self.assertEqual(json.loads(outcome.stdout)["status"], "BLOCKED")
        self.assertNotIn(str(self.root), outcome.stdout)
        self.assertNotIn("missing.md", outcome.stdout)

    def test_reject_bad_version_mapping_cli_before_metadata_access(self):
        out = subprocess.run(
            [sys.executable, str(TOOLS / "flowpilot_csv_e2e.py"),
             "--backend", "projectready-local-metadata", "--goal", "버전 비교",
             "--root", str(self.root), "--required", "README.md",
             "--candidate", "../private=README.md", "--approval", "APPROVE_LOCAL_METADATA"],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(out.returncode, 2, out.stderr)
        self.assertEqual(json.loads(out.stdout)["status"], "REFUSED")
        self.assertNotIn(str(self.root), out.stdout)


if __name__ == "__main__":
    unittest.main()
