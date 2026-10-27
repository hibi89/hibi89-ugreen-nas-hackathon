import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flowpilot.evidence import Observed, ObservationBatch, report, ItemState, Overall, safe_path


def obs(path, ref="id://1", **kw):
    return Observed(path, ref, contained=True, **kw)


def good(*entries, **kw):
    return ObservationBatch("approved-root-opaque", tuple(entries), permission_confirmed=True,
                            registered_adapter_confirmed=True, scan_complete=True,
                            pagination_complete=True, **kw)


class EvidenceTests(unittest.TestCase):
    def test_present_simulated(self):
        r = report(["files/a.pdf"], good(obs("files/a.pdf")))
        self.assertEqual(r.items[0].state, ItemState.PRESENT)
        self.assertFalse(r.actual_nas_verified)
        self.assertEqual(r.overall, Overall.NEEDS_REVIEW)

    def test_missing_complete(self):
        r = report(["a.pdf"], good())
        self.assertEqual(r.items[0].state, ItemState.MISSING)
        self.assertEqual(r.overall, Overall.BLOCKED)

    def test_truncated_not_missing(self):
        batch = ObservationBatch("approved-root", (), permission_confirmed=True,
                                 registered_adapter_confirmed=True, scan_complete=True,
                                 pagination_complete=False)
        self.assertEqual(report(["a.pdf"], batch).items[0].state, ItemState.NOT_CHECKED)

    def test_permission_denial_fails_closed(self):
        self.assertEqual(report(["a.pdf"], ObservationBatch("root", (obs("a.pdf"),))).items[0].state,
                         ItemState.NOT_CHECKED)

    def test_failed_scan_fails_closed(self):
        batch = ObservationBatch("root", (obs("a.pdf"),), True, True, True, True, True)
        self.assertEqual(report(["a.pdf"], batch).items[0].state, ItemState.NOT_CHECKED)

    def test_symlink_target_unknown(self):
        batch = good(Observed("a.pdf", "ref", is_symlink=True, contained=None))
        self.assertEqual(report(["a.pdf"], batch).items[0].state, ItemState.NOT_CHECKED)

    def test_target_containment_unknown(self):
        batch = good(Observed("a.pdf", "ref", is_symlink=False, contained=None))
        self.assertEqual(report(["a.pdf"], batch).items[0].state, ItemState.NOT_CHECKED)

    def test_empty_ref_not_present(self):
        self.assertEqual(report(["a.pdf"], good(obs("a.pdf", ""))).items[0].state, ItemState.NOT_CHECKED)

    def test_multiple_final_candidates(self):
        batch = good(obs("a.pdf", "ref-1"), obs("a_v2.pdf", "ref-2"))
        r = report(["a.pdf"], batch, version_candidates={"a.pdf": ["a_v2.pdf"]})
        self.assertEqual(r.items[0].state, ItemState.VERSION_REVIEW)

    def test_duplicate_observations_need_review(self):
        r = report(["a.pdf"], good(obs("a.pdf", "1"), obs("a.pdf", "2")))
        self.assertEqual(r.items[0].state, ItemState.VERSION_REVIEW)

    def test_restricted_path_refused(self):
        for p in (".env", "credentials/token.txt", ".ssh/id_rsa", "config.json", "a/private_key.pem"):
            with self.subTest(p=p), self.assertRaises(ValueError):
                safe_path(p)

    def test_traversal_refused(self):
        for p in ("../a", "a/../b", "a\\b", "/root", "a//b", "a/./b", "a\x00b"):
            with self.subTest(p=p), self.assertRaises(ValueError):
                safe_path(p)

    def test_restricted_observation_cannot_leak(self):
        with self.assertRaises(ValueError):
            report(["a.pdf"], good(obs(".env")))

    def test_out_of_scope_version_rejected(self):
        with self.assertRaises(ValueError):
            report(["a.pdf"], good(), version_candidates={"b.pdf": ("other.pdf",)})

    def test_no_items_rejected(self):
        with self.assertRaises(ValueError):
            report([], good())

    def test_no_side_effects_contract(self):
        r = report(["a.pdf"], good(obs("a.pdf")))
        self.assertFalse(r.actual_nas_verified)
        self.assertIn("NOT_VERIFIED", r.limitations[0])

if __name__ == "__main__":
    unittest.main()
