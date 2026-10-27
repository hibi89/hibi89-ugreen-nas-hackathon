"""G50 pure planning-to-evidence end-to-end synthetic contract."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from flowpilot.pipeline import evaluate_offline
from flowpilot.evidence import ObservationBatch,Observed,ItemState

ROOT_DIR='/volume1/projects/alpha'
BASE={'request':'handoff deliverables','root':ROOT_DIR,'required_paths':('README.md','release/output.pdf'),
      'metadata_approved':True,'unknown_processing_accepted':True}

def fixture(*observations,root=ROOT_DIR,complete=True):
    return ObservationBatch(root,tuple(observations),True,True,complete,complete)

def seen(path,ref):return Observed(path,ref,contained=True)

class FlowPilotPipeline(unittest.TestCase):
    def test_no_metadata_approval(self):
        x=evaluate_offline(**{**BASE,'metadata_approved':False},batch=fixture())
        self.assertEqual(x.status,'WAITING_APPROVAL');self.assertIsNone(x.report)

    def test_no_claimed_processing_consent(self):
        x=evaluate_offline(**{**BASE,'unknown_processing_accepted':False},batch=fixture())
        self.assertEqual(x.status,'WAITING_APPROVAL')

    def test_no_runtime_adapter_no_fake_results(self):
        x=evaluate_offline(**BASE)
        self.assertEqual(x.status,'NEEDS_REVIEW');self.assertIn('NO_OBSERVED_METADATA',x.limitations)

    def test_root_mismatch_blocks(self):
        x=evaluate_offline(**BASE,batch=fixture(root='/volume1/projects/other'))
        self.assertEqual(x.status,'BLOCKED');self.assertIsNone(x.report)

    def test_all_present_cannot_claim_real_nas_ready(self):
        x=evaluate_offline(**BASE,batch=fixture(seen('README.md','synthetic://a'),seen('release/output.pdf','synthetic://b')))
        self.assertEqual(x.status,'NEEDS_REVIEW');self.assertFalse(x.actual_nas_verified)
        self.assertEqual([i.state for i in x.report.items],[ItemState.PRESENT,ItemState.PRESENT])

    def test_missing_item_blocks_when_complete_claimed(self):
        x=evaluate_offline(**BASE,batch=fixture(seen('README.md','synthetic://a')))
        self.assertEqual(x.status,'BLOCKED');self.assertEqual(x.report.items[1].state,ItemState.MISSING)

    def test_partial_no_missing_claim(self):
        x=evaluate_offline(**BASE,batch=fixture(complete=False))
        self.assertEqual(x.status,'NEEDS_REVIEW');self.assertEqual(x.report.items[0].state,ItemState.NOT_CHECKED)

    def test_cross_source_document_ref_cannot_be_injected(self):
        x=evaluate_offline(**{**BASE,'request':'summarize document'},batch=fixture(seen('README.md','synthetic://good')),document_approved=True,returned_document_refs=('synthetic://evil',))
        self.assertEqual(x.status,'BLOCKED');self.assertIn('UNATTRIBUTABLE_DOCUMENT_REFERENCE',x.limitations)

    def test_approved_document_ref_still_not_nas_validation(self):
        x=evaluate_offline(**{**BASE,'request':'summarize document'},batch=fixture(seen('README.md','synthetic://a'),seen('release/output.pdf','synthetic://b')),document_approved=True,returned_document_refs=('synthetic://a',))
        self.assertEqual(x.status,'NEEDS_REVIEW');self.assertEqual([s.id for s in x.plan.steps],['inventory','document','report'])

    def test_writes_blocked_before_evidence(self):
        x=evaluate_offline(**{**BASE,'request':'파일 삭제해줘'},batch=fixture(seen('README.md','synthetic://a')))
        self.assertEqual(x.status,'BLOCKED');self.assertIsNone(x.report)

if __name__=='__main__':unittest.main()
