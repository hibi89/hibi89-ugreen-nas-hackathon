"""G249 real disposable local filesystem / create-only report regression."""
from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_g249_version_export import run, _evidence, ExportRefused


class G249VersionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "approved-local"
        self.root.mkdir()
        self.first = self.root / "final.pdf"
        self.second = self.root / "final_v2.pdf"
        self.first.write_bytes(b"original synthetic version one")
        self.second.write_bytes(b"original synthetic version two")
        self.report = self.base / "evidence.json"
        self.kw = {"root": self.root, "required": ["final.pdf"],
                   "candidates": ["final.pdf=final_v2.pdf"], "output": self.report}

    def test_no_metadata_consent_means_no_source_or_output_access(self):
        result = run(**self.kw)
        self.assertEqual(result["status"], "WAITING_LOCAL_METADATA_APPROVAL")
        self.assertFalse(self.report.exists())
        self.assertEqual(self.first.read_bytes(), b"original synthetic version one")

    def test_distinct_report_creation_consent(self):
        result = run(**self.kw, approve_metadata=True)
        self.assertEqual(result["status"], "WAITING_SEPARATE_REPORT_CREATION_APPROVAL")
        self.assertFalse(self.report.exists())
        self.assertEqual(result["findings"], [{"index": 1, "state": "VERSION_REVIEW"}])

    def test_real_version_report_is_private_create_only_and_manual(self):
        result = run(**self.kw, approve_metadata=True, approve_create=True)
        self.assertTrue(result["output_created"])
        self.assertEqual(result["status"], "LOCAL_VERSION_EVIDENCE_CREATED_NOT_NAS")
        raw = self.report.read_text("ascii")
        self.assertNotIn(str(self.root), raw)
        self.assertNotIn("final.pdf", raw)
        self.assertNotIn("final_v2.pdf", raw)
        self.assertNotIn("original synthetic", raw)
        doc = json.loads(raw)
        self.assertEqual(doc["findings"], [{"index": 1, "state": "VERSION_REVIEW"}])
        self.assertTrue(doc["manual_owner_review_required"])
        self.assertFalse(doc["auto_selected_final_version"])
        self.assertFalse(doc["nas_verified"])
        self.assertFalse(doc["owner_file_contents_opened"])
        self.assertEqual(self.first.read_bytes(), b"original synthetic version one")
        self.assertEqual(self.second.read_bytes(), b"original synthetic version two")

    def test_existing_report_never_overwritten(self):
        self.report.write_bytes(b"existing owner report")
        with self.assertRaisesRegex(ExportRefused, "CREATE_ONLY_OUTPUT_REFUSED"):
            run(**self.kw, approve_metadata=True, approve_create=True)
        self.assertEqual(self.report.read_bytes(), b"existing owner report")

    def test_no_create_without_metadata_approval(self):
        with self.assertRaisesRegex(ExportRefused, "TWO_DISTINCT_APPROVALS_REQUIRED"):
            run(**self.kw, approve_create=True)
        self.assertFalse(self.report.exists())

    def test_missing_candidates_fail_before_source_lookup(self):
        with self.assertRaises(ExportRefused):
            run(self.root, ["final.pdf"], [], self.report,
                approve_metadata=True, approve_create=True)
        self.assertFalse(self.report.exists())

    def test_traversal_candidate_refused_without_leaking_path(self):
        with self.assertRaisesRegex(ExportRefused, "LOCAL_VERSION_INSPECTION_REFUSED"):
            run(self.root, ["final.pdf"], ["final.pdf=../secret.pdf"], self.report,
                approve_metadata=True, approve_create=True)
        self.assertFalse(self.report.exists())

    def test_output_symlink_parent_refused(self):
        link = self.base / "linked"
        try:
            link.symlink_to(self.base, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("Symlink unavailable under this platform policy")
        with self.assertRaisesRegex(ExportRefused, "OUTPUT_PARENT_LINK_REFUSED"):
            run(self.root, ["final.pdf"], ["final.pdf=final_v2.pdf"],
                link / "evidence.json", approve_metadata=True, approve_create=True)

    def test_invalid_evidence_refused(self):
        with self.assertRaises(ExportRefused):
            _evidence({"status": "WAITING_APPROVAL", "inspection_result": []})


if __name__ == "__main__":
    unittest.main()
