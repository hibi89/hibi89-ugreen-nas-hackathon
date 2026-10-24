"""End-to-end synthetic contract tests for provisional G4 assembly."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from projectready.combined_report import assemble
from projectready.policy_guard import Policy
from projectready.presence import EvidenceOrigin, FileEvidence, ScanEnvelope
from projectready.readiness import Overall, Requirement, ScanStatus, Verdict
from projectready.version_candidates import VersionSignal

R=(Requirement("deliverable","final/brief.pdf"),)
def simulated(*paths):
    return ScanEnvelope(authorized_root_ref="SIM_ROOT",scope_prefix="final",status=ScanStatus.COMPLETE,
        evidence_origin=EvidenceOrigin.SDK_VERIFIED,adapter_verified=True,
        permission_granted=True,pagination_exhausted=True,complete_scope=True,
        observations=tuple(FileEvidence(x,"test-ref-"+str(i)) for i,x in enumerate(paths)),
        scan_reference="simulated-scan")
P=Policy(folder_selected=True,authorized_metadata_read=True,official_adapter_validated=True)

class CombinedTests(unittest.TestCase):
    def test_present_is_not_ready_without_real_privacy_and_version(self):
        out=assemble(R,simulated("final/brief.pdf"),P)
        self.assertEqual(Overall.NEEDS_REVIEW,out.overall)
        self.assertFalse(out.is_real_nas_validation)
        self.assertEqual(Verdict.NOT_CHECKED,out.privacy_check)
        self.assertEqual(Verdict.NOT_CHECKED,out.version_verification)
    def test_proven_missing_blocks_simulation(self):
        out=assemble(R,simulated(),P)
        self.assertEqual(Overall.BLOCKED,out.overall)
        self.assertEqual(Verdict.FAIL,out.presence.checks[0].verdict)
    def test_version_competitors_need_review(self):
        out=assemble(R,simulated("final/brief.pdf","final/brief_v2.pdf"),P)
        self.assertEqual(VersionSignal.CANDIDATES_REVIEW,out.versions[0].signal)
        self.assertEqual(Overall.NEEDS_REVIEW,out.overall)
    def test_incomplete_scan_never_false_blocks(self):
        out=assemble(R,replace(simulated(),status=ScanStatus.PARTIAL),P)
        self.assertEqual(Overall.NEEDS_REVIEW,out.overall)
    def test_unverified_adapter_never_ready(self):
        out=assemble(R,replace(simulated("final/brief.pdf"),adapter_verified=False),P)
        self.assertEqual(Overall.NEEDS_REVIEW,out.overall)
        self.assertEqual(Verdict.NOT_CHECKED,out.presence.checks[0].verdict)
    def test_scope_permission_denied_never_ready(self):
        out=assemble(R,replace(simulated("final/brief.pdf"),permission_granted=False),P)
        self.assertEqual(Overall.NEEDS_REVIEW,out.overall)
    def test_missing_policy_consent_never_ready(self):
        out=assemble(R,simulated("final/brief.pdf"),replace(P,authorized_metadata_read=False))
        self.assertEqual(Overall.NEEDS_REVIEW,out.overall)
    def test_partial_report_explains_limitations(self):
        out=assemble(R,replace(simulated(),status=ScanStatus.PARTIAL),P)
        self.assertTrue(out.limitations)
        self.assertIn("Sensitive-content disclosure validation NOT_CHECKED",out.limitations)
    def test_multiple_required_file_mixed_missing_blocks(self):
        more=(R[0],Requirement("invoice","final/invoice.pdf"))
        out=assemble(more,simulated("final/brief.pdf"),P)
        self.assertEqual(Overall.BLOCKED,out.overall)
        self.assertEqual([Verdict.PASS,Verdict.FAIL],[c.verdict for c in out.presence.checks])
    def test_invalid_scope_rejected(self):
        with self.assertRaises(ValueError):
            assemble(R,replace(simulated(),scope_prefix="another"),P)

if __name__=="__main__":
    unittest.main()
