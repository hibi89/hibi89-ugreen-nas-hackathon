"""Filename variant signals are never authoritative version proofs."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from projectready.version_candidates import VersionSignal, detect_version_candidates
from projectready.presence import EvidenceOrigin, FileEvidence, ScanEnvelope
from projectready.readiness import Requirement, ScanStatus

R=Requirement("design", "final/design.pdf")
def snap(*paths):
    return ScanEnvelope(
        authorized_root_ref="MOCK_ROOT",
        scope_prefix="final",
        status=ScanStatus.COMPLETE,
        evidence_origin=EvidenceOrigin.SDK_VERIFIED,
        adapter_verified=True, permission_granted=True,
        pagination_exhausted=True,complete_scope=True,
        observations=tuple(FileEvidence(p,f"mock://{i}") for i,p in enumerate(paths)),
        scan_reference="mock://scan"
    )

class VersionCandidateTests(unittest.TestCase):
    def test_exact_and_v2_flags_review(self):
        out=detect_version_candidates(R,snap("final/design.pdf","final/design_v2.pdf"))
        self.assertEqual(VersionSignal.CANDIDATES_REVIEW,out.signal)
        self.assertFalse(out.authoritatively_verified_current_version)
    def test_final_draft_triggers_review(self):
        out=detect_version_candidates(R,snap("final/design_final.pdf","final/design_draft.pdf"))
        self.assertEqual(VersionSignal.CANDIDATES_REVIEW,out.signal)
    def test_recognizes_chained_final_v2(self):
        out=detect_version_candidates(R,snap("final/design_final_v2.pdf","final/design_v3.pdf"))
        self.assertEqual(VersionSignal.CANDIDATES_REVIEW,out.signal)
    def test_different_family_does_not_group(self):
        out=detect_version_candidates(R,snap("final/design.pdf","final/design2.pdf"))
        self.assertEqual(VersionSignal.NONE_DETECTED,out.signal)
    def test_different_dir_rejected_not_silently_scanned(self):
        with self.assertRaises(ValueError):
            detect_version_candidates(R,snap("final/design.pdf","other/design_v2.pdf"))
    def test_different_extension_does_not_group(self):
        out=detect_version_candidates(R,snap("final/design.pdf","final/design.docx"))
        self.assertEqual(VersionSignal.NONE_DETECTED,out.signal)
    def test_filename_single_is_not_authoritative_proof(self):
        out=detect_version_candidates(R,snap("final/design.pdf"))
        self.assertEqual(VersionSignal.NONE_DETECTED,out.signal)
        self.assertFalse(out.authoritatively_verified_current_version)
    def test_empty_candidate_no_latest_claim(self):
        out=detect_version_candidates(R,snap("final/unrelated.pdf"))
        self.assertEqual(VersionSignal.NONE_DETECTED,out.signal)
        self.assertFalse(out.authoritatively_verified_current_version)
    def test_missing_sdk_proof_is_not_checked(self):
        out=detect_version_candidates(R,replace(snap("final/design.pdf"),adapter_verified=False))
        self.assertEqual(VersionSignal.NOT_CHECKED,out.signal)
    def test_partial_page_is_not_checked(self):
        out=detect_version_candidates(R,replace(snap("final/design.pdf"),status=ScanStatus.PARTIAL))
        self.assertEqual(VersionSignal.NOT_CHECKED,out.signal)
    def test_pagination_gap_is_not_checked(self):
        out=detect_version_candidates(R,replace(snap("final/design.pdf"),pagination_exhausted=False))
        self.assertEqual(VersionSignal.NOT_CHECKED,out.signal)
    def test_no_consent_is_not_checked(self):
        out=detect_version_candidates(R,replace(snap("final/design.pdf"),permission_granted=False))
        self.assertEqual(VersionSignal.NOT_CHECKED,out.signal)
    def test_no_evidence_reference_is_not_checked(self):
        out=detect_version_candidates(R,replace(snap("final/design.pdf"),observations=(FileEvidence("final/design.pdf",""),)))
        self.assertEqual(VersionSignal.NOT_CHECKED,out.signal)
    def test_path_traversal_fails(self):
        with self.assertRaises(ValueError):
            detect_version_candidates(R,snap("final/../private/key"))
    def test_case_folding_only_for_candidate_signal(self):
        out=detect_version_candidates(R,snap("final/design.pdf","final/DESIGN_V2.PDF"))
        self.assertEqual(VersionSignal.CANDIDATES_REVIEW,out.signal)

if __name__=="__main__":
    unittest.main()
