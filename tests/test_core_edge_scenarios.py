"""G5 two core plus one edge scenario: SYNTHETIC ONLY, NOT OFFICIAL UGREEN."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from projectready.combined_report import assemble
from projectready.policy_guard import Policy
from projectready.presence import EvidenceOrigin, FileEvidence, ScanEnvelope
from projectready.readiness import Overall, Requirement, ScanStatus, Verdict

REQUIRED=(Requirement("design","delivery/design.pdf"),Requirement("contract","delivery/contract.pdf"))
POLICY=Policy(folder_selected=True,authorized_metadata_read=True,official_adapter_validated=True)
def fixture(*paths):
    return ScanEnvelope(authorized_root_ref="MOCK_ONLY",
        scope_prefix="delivery",status=ScanStatus.COMPLETE,
        evidence_origin=EvidenceOrigin.SDK_VERIFIED,
        adapter_verified=True,permission_granted=True,
        pagination_exhausted=True,complete_scope=True,
        observations=tuple(FileEvidence(p,"mock-ref-"+str(i)) for i,p in enumerate(paths)),
        scan_reference="mock-scan")

class SubmissionScenarios(unittest.TestCase):
    def test_core1_all_files_present_but_requires_independent_gates(self):
        result=assemble(REQUIRED,fixture("delivery/design.pdf","delivery/contract.pdf"),POLICY)
        self.assertEqual(Overall.NEEDS_REVIEW,result.overall)
        self.assertEqual([Verdict.PASS]*2,[x.verdict for x in result.presence.checks])
        self.assertEqual(Verdict.NOT_CHECKED,result.privacy_check)
        self.assertFalse(result.is_real_nas_validation)

    def test_core2_required_contract_absent_in_complete_scan_blocks(self):
        result=assemble(REQUIRED,fixture("delivery/design.pdf"),POLICY)
        self.assertEqual(Overall.BLOCKED,result.overall)
        self.assertEqual(Verdict.FAIL,result.presence.checks[1].verdict)

    def test_edge1_permission_denial_prevents_absence_claim(self):
        scan=replace(fixture(),status=ScanStatus.DENIED,permission_granted=False)
        result=assemble(REQUIRED,scan,POLICY)
        self.assertEqual(Overall.NEEDS_REVIEW,result.overall)
        self.assertEqual([Verdict.NOT_CHECKED]*2,[x.verdict for x in result.presence.checks])

if __name__=="__main__":
    unittest.main()
