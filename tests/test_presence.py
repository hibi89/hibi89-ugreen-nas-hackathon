"""Synthetic checks only: no SDK, NAS, real adapter or customer files."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from projectready.presence import EvidenceOrigin, FileEvidence, ScanEnvelope, check_presence
from projectready.readiness import Requirement, ScanStatus, Verdict

REQUESTS=(Requirement("design", "deliverables/design.pdf"), Requirement("quote", "deliverables/quote.pdf"))
OBS=(FileEvidence("deliverables/design.pdf", "mock://evidence/design"),FileEvidence("deliverables/quote.pdf", "mock://evidence/quote"))
MOCK=ScanEnvelope(
    authorized_root_ref="SYNTHETIC_ROOT_ONLY",
    scope_prefix="deliverables",
    status=ScanStatus.COMPLETE,
    evidence_origin=EvidenceOrigin.SDK_VERIFIED,  # Simulates future adapter, not real.
    adapter_verified=True, permission_granted=True,
    pagination_exhausted=True, complete_scope=True,
    observations=OBS, scan_reference="mock://scan/one",
)

class PresenceContractTests(unittest.TestCase):
    def test_mock_fully_verified_present(self):
        out=check_presence(REQUESTS, MOCK)
        self.assertEqual([Verdict.PASS,Verdict.PASS],[x.verdict for x in out.checks])
        self.assertEqual(("mock://evidence/design",),out.checks[0].evidence_refs)
    def test_unverified_adapter_never_passes(self):
        out=check_presence(REQUESTS, replace(MOCK,adapter_verified=False))
        self.assertEqual([Verdict.NOT_CHECKED]*2,[x.verdict for x in out.checks])
    def test_synthetic_origin_never_passes(self):
        out=check_presence(REQUESTS, replace(MOCK,evidence_origin=EvidenceOrigin.SYNTHETIC))
        self.assertFalse(out.trusted)
    def test_missing_in_complete_mock_scan_is_fail(self):
        out=check_presence(REQUESTS,replace(MOCK,observations=OBS[:1]))
        self.assertEqual(Verdict.FAIL,out.checks[1].verdict)
    def test_missing_in_partial_scan_is_unknown(self):
        out=check_presence(REQUESTS,replace(MOCK,status=ScanStatus.PARTIAL,observations=OBS[:1]))
        self.assertEqual(Verdict.NOT_CHECKED,out.checks[1].verdict)
    def test_unexhausted_pagination_never_proves_absence(self):
        out=check_presence(REQUESTS,replace(MOCK,pagination_exhausted=False,observations=OBS[:1]))
        self.assertEqual(Verdict.NOT_CHECKED,out.checks[1].verdict)
    def test_scope_incomplete_never_proves_absence(self):
        out=check_presence(REQUESTS,replace(MOCK,complete_scope=False,observations=OBS[:1]))
        self.assertEqual(Verdict.NOT_CHECKED,out.checks[1].verdict)
    def test_denied_cannot_pass_even_with_observed_names(self):
        out=check_presence(REQUESTS,replace(MOCK,status=ScanStatus.DENIED))
        self.assertEqual([Verdict.NOT_CHECKED]*2,[x.verdict for x in out.checks])
    def test_no_consent_fails_closed(self):
        out=check_presence(REQUESTS,replace(MOCK,permission_granted=False))
        self.assertEqual(Verdict.NOT_CHECKED,out.checks[0].verdict)
    def test_no_scan_reference_fails_closed(self):
        out=check_presence(REQUESTS,replace(MOCK,scan_reference=""))
        self.assertEqual(Verdict.NOT_CHECKED,out.checks[0].verdict)
    def test_no_file_evidence_reference_fails_closed(self):
        out=check_presence(REQUESTS,replace(MOCK,observations=(FileEvidence("deliverables/design.pdf", ""),OBS[1])))
        self.assertEqual(Verdict.NOT_CHECKED,out.checks[0].verdict)
    def test_directory_is_not_deliverable_file(self):
        out=check_presence(REQUESTS,replace(MOCK,observations=(FileEvidence("deliverables/design.pdf","mock://dir",False),OBS[1])))
        self.assertEqual(Verdict.NOT_CHECKED,out.checks[0].verdict)
    def test_duplicate_conflicting_observations_flagged(self):
        duplicate=(OBS[0],OBS[0],OBS[1])
        out=check_presence(REQUESTS,replace(MOCK,observations=duplicate))
        self.assertEqual(Verdict.REVIEW,out.checks[0].verdict)
    def test_case_sensitive_exact(self):
        out=check_presence(REQUESTS,replace(MOCK,observations=(FileEvidence("deliverables/Design.pdf","mock://name"),OBS[1])))
        self.assertEqual(Verdict.FAIL,out.checks[0].verdict)
    def test_scope_prefix_segment_boundary(self):
        with self.assertRaises(ValueError):
            check_presence((Requirement("outside","deliverables-private/a"),),MOCK)
    def test_outside_observation_rejected(self):
        with self.assertRaises(ValueError):
            check_presence(REQUESTS,replace(MOCK,observations=(FileEvidence("secrets/token","mock://x"),)))
    def test_traversal_requirement_rejected(self):
        with self.assertRaises(ValueError):
            check_presence((Requirement("bad","deliverables/../secrets"),),MOCK)
    def test_traversal_observation_rejected(self):
        with self.assertRaises(ValueError):
            check_presence(REQUESTS,replace(MOCK,observations=(FileEvidence("deliverables/../secret","mock://a"),)))
    def test_empty_requirements_rejected(self):
        with self.assertRaises(ValueError):
            check_presence((),MOCK)
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            check_presence((REQUESTS[0],REQUESTS[0]),MOCK)
    def test_missing_authorized_root_rejected(self):
        with self.assertRaises(ValueError):
            check_presence(REQUESTS,replace(MOCK,authorized_root_ref=""))
    def test_does_not_mutate_fixture(self):
        before=MOCK
        check_presence(REQUESTS,MOCK)
        self.assertEqual(MOCK,before)

if __name__=="__main__":
    unittest.main()
