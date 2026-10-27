"""G47: offline adversarial safety regression; NEVER a real NAS test."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flowpilot.planner import draft_plan, State
from flowpilot.evidence import safe_path, report, Observed, ObservationBatch, ItemState

P = dict(root="/volume1/projects/alpha", required_paths=("README.md",),
         metadata_approved=True, unknown_processing_accepted=True)


class FlowPilotG47Security(unittest.TestCase):
    def test_conjugated_korean_write_commands_refused(self):
        for goal in ("파일 확인 후 삭제해줘", "파일 업로드해줘", "파일을 이동해줘",
                     "파일 복사하고 정리해줘", "파일 공유해줘"):
            with self.subTest(goal=goal):
                self.assertEqual(draft_plan(goal, **P).state, State.BLOCKED)

    def test_english_write_commands_refused(self):
        for goal in ("Check file then publish", "Check and copy files", "Erase the file"):
            with self.subTest(goal=goal):
                self.assertEqual(draft_plan(goal, **P).state, State.BLOCKED)

    def test_sensitive_filenames_rejected_in_both_engines(self):
        paths = ("secrets.txt", "credentials.json", "passwords.csv", ".aws/credentials",
                 "data/.kube/config", "authorized_keys", "known_hosts", ".npmrc",
                 ".netrc", "logs/sessions.json", "access_key.txt", "service_account.json")
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    safe_path(path)
                with self.assertRaises(ValueError):
                    draft_plan("check files", required_paths=(path,), root=P["root"],
                               metadata_approved=True, unknown_processing_accepted=True)

    def test_bidi_and_invisible_unicode_refused(self):
        for path in ("hello\u202egpj.txt", "a\u200db.pdf"):
            with self.subTest(path=repr(path)):
                with self.assertRaises(ValueError):
                    safe_path(path)
                with self.assertRaises(ValueError):
                    draft_plan("check files", required_paths=(path,), root=P["root"],
                               metadata_approved=True, unknown_processing_accepted=True)

    def test_encoded_and_alt_stream_paths_refused(self):
        for path in ("%2e%2e/secret.txt", "folder/%2F/target", "report.pdf:secret"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    safe_path(path)
                with self.assertRaises(ValueError):
                    draft_plan("check files", required_paths=(path,), root=P["root"],
                               metadata_approved=True, unknown_processing_accepted=True)

    def test_restricted_observation_fails_before_report(self):
        b = ObservationBatch("scoped-root", (Observed("data/secrets.txt", "id1", contained=True),),
                             permission_confirmed=True, registered_adapter_confirmed=True,
                             scan_complete=True, pagination_complete=True)
        with self.assertRaises(ValueError):
            report(("out/a.pdf",), b)

    def test_normal_read_only_request_still_accepted(self):
        result = draft_plan("프로젝트 파일 확인해줘", **P)
        self.assertEqual(result.state, State.READY_FOR_ADAPTER_CHECK)
        for path in ("data/release_v2.pdf", "report/summary.md", "out/2026_10_27.csv"):
            self.assertEqual(safe_path(path), path)

    def test_incomplete_scan_cannot_prove_absence(self):
        batch = ObservationBatch("scoped-root", (), permission_confirmed=True,
                                 registered_adapter_confirmed=True, scan_complete=False,
                                 pagination_complete=False)
        self.assertEqual(report(("out/a.pdf",), batch).items[0].state, ItemState.NOT_CHECKED)


if __name__ == "__main__":
    unittest.main()
