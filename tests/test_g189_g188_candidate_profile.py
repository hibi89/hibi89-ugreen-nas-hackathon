"""G189 G188 SHA-pinned optional candidate CLI profile boundary.

All sources in this suite are *synthetic fixtures*. No private candidate bytes,
official vendor code, real Docker, NAS runtime or network traffic is exercised.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot3_official_checker as gate


def make_zip(files):
    memory = BytesIO()
    with ZipFile(memory, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return memory.getvalue()


class G189ExactG188ProfileTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.skill = b"---\nname: flowpilot-3\ndescription: synthetic test\n---\n# Goal\n"
        self.files = {gate.MEMBER: self.skill,
                      gate.G139_MEMBERS[1]: b"# Fixture 1\n",
                      gate.G139_MEMBERS[2]: b"# Fixture 2\n"}
        self.candidate = self.root / "owner-draft.zip"
        self.candidate.write_bytes(make_zip(self.files))
        self.vendor = self.root / "vendor.zip"
        self.vendor.write_bytes(make_zip({
            "uliya-skill-kit/SKILL.md": b"# synthetic toolkit",
            "uliya-skill-kit/scripts/check-skill.mjs": b"// fixture, NEVER run",
            "uliya-skill-kit/data/capability-catalog.json": b"{}",
        }))

    def patched(self, *, candidate_zip=None, source=None):
        candidate_zip = candidate_zip or self.candidate.read_bytes()
        source = source or self.skill
        mocks = [patch.object(gate, "G188_CANDIDATE_SHA", sha256(source).hexdigest()),
                 patch.object(gate, "G188_CANDIDATE_ZIP_SHA", sha256(candidate_zip).hexdigest()),
                 patch.object(gate, "VENDOR_ZIP_SHA", sha256(self.vendor.read_bytes()).hexdigest())]
        for m in mocks:
            m.start()
            self.addCleanup(m.stop)

    def test_hardcoded_real_pins_and_original_g147_are_unchanged(self):
        self.assertEqual(gate.G188_CANDIDATE_SHA,
                         "4baf816e7deafa7dec544d93209f8ae3d1fb6400515212d2eb1d9b5fe0f6acca")
        self.assertEqual(gate.G188_CANDIDATE_ZIP_SHA,
                         "568ad542d829b07ca910ca974ca39f2c29ed210558a40354b6518cabfc73ceef")
        self.assertEqual(gate.G147_CANDIDATE_ZIP_SHA,
                         "d8c66b24000b6fb1f7ea8b0d69417febfc83128d935e9b8db33dd382bb9c64c1")

    def test_g188_inspect_exact_members_and_no_vendor_execution(self):
        self.patched()
        with patch.object(gate, "_execute", side_effect=AssertionError("vendor executed")):
            report = gate.check(self.candidate, self.vendor, candidate_profile="g188", mode="inspect")
        self.assertEqual(report["candidate_profile"], "g188")
        self.assertEqual(report["source_sha256"], sha256(self.skill).hexdigest())
        self.assertEqual(report["candidate_member_count"], 3)
        self.assertEqual(report["status"], "EXACT_SOURCE_AND_VENDOR_PIN_VERIFIED_NO_CHECKER_RUN")
        self.assertFalse(report["official_checker_executed"])
        self.assertEqual(report["release_gate"], "HOLD")

    def test_modified_zip_is_refused_against_unchanged_pin(self):
        self.patched()
        self.candidate.write_bytes(self.candidate.read_bytes() + b"tamper")
        with self.assertRaisesRegex(gate.VerificationRefused, "SHA256 mismatch"):
            gate.check(self.candidate, self.vendor, candidate_profile="g188", mode="inspect")

    def test_modified_skill_even_with_rehashed_zip_is_refused(self):
        self.patched()
        changed = dict(self.files, **{gate.MEMBER: b"not the expected source"})
        self.candidate.write_bytes(make_zip(changed))
        with patch.object(gate, "G188_CANDIDATE_ZIP_SHA",
                          sha256(self.candidate.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(gate.VerificationRefused, "Skill bytes differ"):
                gate.check(self.candidate, self.vendor, candidate_profile="g188", mode="inspect")

    def test_missing_reference_even_with_rehashed_zip_is_refused(self):
        self.patched()
        self.candidate.write_bytes(make_zip({gate.MEMBER: self.skill,
                                              gate.G139_MEMBERS[1]: b"only one reference"}))
        with patch.object(gate, "G188_CANDIDATE_ZIP_SHA",
                          sha256(self.candidate.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(gate.VerificationRefused, "exact Markdown"):
                gate.check(self.candidate, self.vendor, candidate_profile="g188", mode="inspect")

    def test_unapproved_docker_is_rejected_before_reading(self):
        buf = StringIO()
        args = ["--candidate-zip", str(self.candidate), "--official-kit-zip",
                str(self.vendor), "--candidate-profile", "g188", "--mode", "docker"]
        with patch.object(gate, "check", side_effect=AssertionError("read attempted")) as call, \
             redirect_stdout(buf):
            status = gate.main(args)
        self.assertEqual(status, 2)
        call.assert_not_called()
        report = json.loads(buf.getvalue())
        self.assertFalse(report["official_checker_executed"])
        self.assertEqual(report["release_gate"], "HOLD")

    def test_unapproved_native_is_rejected_before_reading(self):
        buf = StringIO()
        args = ["--candidate-zip", str(self.candidate), "--official-kit-zip",
                str(self.vendor), "--candidate-profile", "g188", "--mode", "native",
                "--accept-native-code-execution-risk"]
        with patch.object(gate, "check", side_effect=AssertionError("read attempted")) as call, \
             redirect_stdout(buf):
            status = gate.main(args)
        self.assertEqual(status, 2)
        call.assert_not_called()
        self.assertEqual(json.loads(buf.getvalue())["release_gate"], "HOLD")

    def test_explicit_docker_optin_only_routes_to_existing_gate_in_mock(self):
        buf = StringIO()
        args = ["--candidate-zip", str(self.candidate), "--official-kit-zip",
                str(self.vendor), "--candidate-profile", "g188", "--mode", "docker",
                "--accept-official-code-execution-risk"]
        with patch.object(gate, "check", return_value={
            "status": "EXACT_SOURCE_AND_VENDOR_PIN_VERIFIED_NO_CHECKER_RUN",
            "official_checker_executed": False, "release_gate": "HOLD",
        }) as call, redirect_stdout(buf):
            status = gate.main(args)
        self.assertEqual(status, 2)
        call.assert_called_once()
        self.assertEqual(call.call_args.kwargs["candidate_profile"], "g188")
        self.assertEqual(call.call_args.kwargs["mode"], "docker")
        self.assertIs(call.call_args.kwargs["official_risk_approved"], True)
        self.assertEqual(json.loads(buf.getvalue())["release_gate"], "HOLD")


if __name__ == "__main__":
    unittest.main()
