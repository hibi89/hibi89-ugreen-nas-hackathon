"""Local provenance gate for the optional private HAE + public SOVIA proof.

Uses disposable git repositories, not the owner's worktrees.
The real HAE execution requires an owner-trusted checkout and is NOT run here.
"""
from __future__ import annotations

from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.verify_private_hae_chain import (
    ProofRefused, main, verify_checkout, EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA
)


def git(root: Path, *args: str):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, check=True, text=True, timeout=10
    ).stdout.strip()


class PrivateSourceGateTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="ugreen-git-gate-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.project = self.root / "fake-private-source"
        self.project.mkdir()
        git(self.project, "init", "-q")
        git(self.project, "config", "user.name", "Synthetic UGREEN CI")
        git(self.project, "config", "user.email", "synthetic@example.invalid")
        self.source = self.project / "packages" / "lightning-azent"
        self.source.mkdir(parents=True)
        (self.source / "example.txt").write_text(
            "synthetic project fixture, not HAE source", encoding="utf-8"
        )
        git(self.project, "add", "packages/lightning-azent/example.txt")
        git(self.project, "commit", "-qm", "test fixture")
        self.sha = git(self.project, "rev-parse", "HEAD")

    def check(self, sha=None, root=None):
        return verify_checkout(
            self.project if root is None else root,
            self.sha if sha is None else sha,
            ("packages/lightning-azent",),
        )

    def test_exact_clean_checkout_accepted(self):
        self.assertEqual(self.check(), self.project.resolve())

    def test_wrong_commit_rejected(self):
        with self.assertRaisesRegex(ProofRefused, "SOURCE_SHA_MISMATCH"):
            self.check(sha="0" * 40)

    def test_modified_tracked_source_rejected(self):
        (self.source / "example.txt").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ProofRefused, "SOURCE_FILES_MODIFIED"):
            self.check()

    def test_untracked_source_rejected(self):
        (self.source / "unexpected.py").write_text("pass", encoding="utf-8")
        with self.assertRaisesRegex(ProofRefused, "SOURCE_FILES_MODIFIED"):
            self.check()

    def test_subdirectory_masquerading_as_checkout_rejected(self):
        with self.assertRaisesRegex(ProofRefused, "SOURCE_ROOT_NOT_GIT_TOPLEVEL"):
            self.check(root=self.source)

    def test_invalid_expected_sha_rejected(self):
        with self.assertRaisesRegex(ProofRefused, "EXPECTED_SOURCE_SHA_INVALID"):
            self.check(sha="not-a-valid-sha")

    def test_missing_checkout_rejected(self):
        with self.assertRaisesRegex(ProofRefused, "SOURCE_ROOT_MISSING"):
            self.check(root=self.root / "no-such-source")

    def test_cli_fail_never_exposes_user_paths(self):
        missing = self.root / "private-customer-folder-name"
        output = io.StringIO()
        with redirect_stderr(output):
            status = main(["--hae-root", str(missing), "--sovia-root", str(missing)])
        result = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["reason_code"], "SOURCE_ROOT_MISSING")
        self.assertEqual(result["release_gate"], "HOLD")
        self.assertNotIn("private-customer-folder-name", output.getvalue())

    def test_pins_are_explicit_full_git_commit_ids(self):
        self.assertEqual(len(EXPECTED_HAE_SHA), 40)
        self.assertEqual(len(EXPECTED_SOVIA_SHA), 40)
        self.assertNotEqual(EXPECTED_HAE_SHA, EXPECTED_SOVIA_SHA)


if __name__ == "__main__":
    unittest.main()
