"""G86 private-runner Git identity and strict receipt contract (offline only).

Fixture scripts and Git repositories are disposable. Never reads real HAE,
Uliya, NAS, customer files or private credentials.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import run_g85_native_backend as entry


def valid_receipt() -> dict:
    return {
        "status": entry.PASS,
        "verification": "G82_PRIVATE_RUNTIME_G83_PUBLIC_ACCEPTANCE",
        "hae_web_git_blob": entry.G82_WEB_BLOB,
        "la_source_commit": entry.LA_COMMIT,
        "ugreen_verifier_commit": entry.G83_PUBLIC_VERIFIER,
        "temporary_zipapp_sha256": "a" * 64,
        "independent_sqlite_payload_verified": True,
        "pending_run_id_bound_to_approval": True,
        "sqlite_business_rows": 2,
        "read_only_recovery_without_duplicate_write": True,
        "original_binary_replaced": False,
        "real_nas_verified": False,
        "devpost_submitted": False,
    }


class G86ReceiptTests(unittest.TestCase):
    def test_exact_receipt_passes_shape_gate(self):
        self.assertTrue(entry._verified_receipt(valid_receipt()))

    def test_status_only_cannot_certify_native_execution(self):
        self.assertFalse(entry._verified_receipt({"status": entry.PASS}))

    def test_negative_provenance_and_type_fail_closed(self):
        cases = [
            ("no-independent-db", "independent_sqlite_payload_verified", False),
            ("no-pending-id", "pending_run_id_bound_to_approval", False),
            ("duplicate-writes", "read_only_recovery_without_duplicate_write", False),
            ("boolean-row-count", "sqlite_business_rows", True),
            ("unexpected-rows", "sqlite_business_rows", 3),
            ("wrong-la", "la_source_commit", "0" * 40),
            ("wrong-web", "hae_web_git_blob", "0" * 40),
            ("wrong-verifier", "ugreen_verifier_commit", "0" * 40),
            ("missing-sha", "temporary_zipapp_sha256", ""),
            ("wrong-sha", "temporary_zipapp_sha256", "z" * 64),
            ("modified-binary", "original_binary_replaced", True),
            ("false-nas-claim", "real_nas_verified", True),
            ("false-submission", "devpost_submitted", True),
        ]
        for label, key, value in cases:
            with self.subTest(case=label):
                receipt = valid_receipt()
                receipt[key] = value
                self.assertFalse(entry._verified_receipt(receipt))

    def test_extraneous_field_rejected_to_prevent_source_leak(self):
        receipt = valid_receipt()
        receipt["private_log"] = "never forward"
        self.assertFalse(entry._verified_receipt(receipt))

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"status":"PASS","status":"FAIL"}',
                       object_pairs_hook=entry._unique_json_object)
        with self.assertRaises(ValueError):
            json.loads('{"count":NaN}', parse_constant=entry._reject_nonfinite)


@unittest.skipUnless(shutil.which("git"), "Git needed for isolated fixture tests")
class G86PrivateScriptTrustTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="g86-private-git-")
        self.addCleanup(self.tmp.cleanup)
        # Exercise the Windows failure case: non-ASCII checkout ancestors.
        self.root = Path(self.tmp.name) / "유그린 해커톤" / "HAE"
        (self.root / "tools").mkdir(parents=True)
        self.git("init", "--quiet")
        self.runner = self.root / "tools" / "g84_verify_ugreen_native.py"
        self.packager = self.root / "tools" / "package_hae_integrated.py"
        self.runner.write_text("# reviewed fake private runner fixture\n", encoding="utf-8")
        self.packager.write_text("# reviewed fake packager fixture\n", encoding="utf-8")
        self.commit("reviewed fixture")
        self.pins = {
            rel: self.git("rev-parse", f"HEAD:{rel}")
            for rel in entry.PINNED_PRIVATE_BLOBS
        }

    def git(self, *args):
        r = subprocess.run(["git", "-C", str(self.root), *args],
                           capture_output=True, text=True, check=True, timeout=12)
        return r.stdout.strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "user.name=G86Fixture", "-c",
                 "user.email=g86-fixture@example.invalid",
                 "commit", "--quiet", "-m", message)

    def check(self):
        with patch.dict(entry.PINNED_PRIVATE_BLOBS, self.pins, clear=True):
            entry._verify_private_source(self.root)

    def test_pinned_clean_private_code_passes(self):
        self.check()

    def test_korean_checkout_root_uses_ascii_only_git_values(self):
        self.assertIn("유그린 해커톤", str(self.root))
        self.assertEqual(entry._git(self.root, "rev-parse", "--show-prefix"), "")
        self.assertEqual(entry._git(self.root, "rev-parse", "--is-inside-work-tree"), "true")
        self.check()

    def test_non_ascii_git_gate_output_fails_closed(self):
        from types import SimpleNamespace
        with patch.object(entry.subprocess, "run", return_value=SimpleNamespace(
            returncode=0, stdout=b"\\xed\\x95\\x9c")):
            with self.assertRaisesRegex(entry.IntegrityRefused, "ASCII gate value"):
                entry._git(self.root, "rev-parse", "--show-prefix")

    def test_docs_only_descendant_keeps_pinned_binary_source(self):
        (self.root / "HANDOFF.md").write_text("documentation\n", encoding="utf-8")
        self.commit("docs only")
        self.check()

    def test_local_modified_runner_refused(self):
        self.runner.write_text("# locally modified\n", encoding="utf-8")
        with self.assertRaisesRegex(entry.IntegrityRefused, "integrity mismatch"):
            self.check()

    def test_committed_runner_change_refused(self):
        self.runner.write_text("# committed altered\n", encoding="utf-8")
        self.commit("changed runner")
        with self.assertRaisesRegex(entry.IntegrityRefused, "integrity mismatch"):
            self.check()

    def test_modified_packager_refused(self):
        self.packager.write_text("# modified package builder\n", encoding="utf-8")
        with self.assertRaisesRegex(entry.IntegrityRefused, "integrity mismatch"):
            self.check()

    def test_wrong_repository_root_refused(self):
        sub = self.root / "nested"
        sub.mkdir()
        with self.assertRaisesRegex(entry.IntegrityRefused, "root mismatch"):
            with patch.dict(entry.PINNED_PRIVATE_BLOBS, self.pins, clear=True):
                entry._verify_private_source(sub)

    def test_non_git_private_runner_is_not_executed(self):
        not_git = Path(self.tmp.name) / "not-git"
        (not_git / "tools").mkdir(parents=True)
        (not_git / "tools" / "g84_verify_ugreen_native.py").write_text(
            "raise RuntimeError('should never execute')\n", encoding="utf-8")
        la = Path(self.tmp.name) / "la"
        (la / "lightning_azent").mkdir(parents=True)
        (la / "lightning_azent" / "__init__.py").write_text("", encoding="utf-8")
        report = entry.run_native(not_git, la, True)
        self.assertEqual(report["status"], "G86_PRIVATE_RUNNER_INTEGRITY_REFUSED")
        self.assertFalse(report["native_verified"])


if __name__ == "__main__":
    unittest.main()
