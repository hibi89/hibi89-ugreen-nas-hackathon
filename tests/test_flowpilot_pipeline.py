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
    def test_g104_selected_handoff_document_is_never_read_without_separate_approval(self):
        root = "/volume1/FLOWPILOT_G104_SYNTHETIC_TEST/project"
        batch = ObservationBatch(root, (
            seen("handoff/summary.md", "synthetic://g104/summary"),
            seen("design/architecture.md", "synthetic://g104/architecture"),
        ), True, True, True, True)
        kwargs = dict(request="summarize handoff/summary.md", root=root,
                      required_paths=("handoff/summary.md",),
                      metadata_approved=True, unknown_processing_accepted=True, batch=batch)
        pending = evaluate_offline(**kwargs, document_approved=False)
        self.assertEqual(pending.status, "NEEDS_REVIEW")
        self.assertNotIn("document", [s.id for s in pending.plan.steps])
        self.assertFalse(pending.actual_nas_verified)
        approved = evaluate_offline(**kwargs, document_approved=True,
                                    returned_document_refs=("synthetic://g104/summary",),
                                    processing_destination_confirmed=True)
        self.assertEqual(approved.status, "NEEDS_REVIEW")
        self.assertIn("document", [s.id for s in approved.plan.steps])
        self.assertFalse(approved.actual_nas_verified)

    def test_g109_content_consent_alone_cannot_plan_unknown_destination(self):
        root = "/volume1/FLOWPILOT_G104_SYNTHETIC_TEST/project"
        batch = ObservationBatch(root, (seen("handoff/summary.md", "synthetic://g104/summary"),),
                                 True, True, True, True)
        kwargs = dict(request="summarize handoff/summary.md", root=root,
                      required_paths=("handoff/summary.md",), metadata_approved=True,
                      unknown_processing_accepted=True, batch=batch,
                      document_approved=True, returned_document_refs=("synthetic://g104/summary",))
        unsafe = evaluate_offline(**kwargs)
        self.assertEqual(unsafe.status, "NEEDS_REVIEW")
        self.assertNotIn("document", [s.id for s in unsafe.plan.steps])
        self.assertIn("DOCUMENT_PROCESSING_DESTINATION_UNVERIFIED", unsafe.plan.limitations)
        confirmed = evaluate_offline(**kwargs, processing_destination_confirmed=True)
        self.assertIn("document", [s.id for s in confirmed.plan.steps])
        self.assertFalse(confirmed.actual_nas_verified)

    def test_g104_missing_signoff_blocks_only_complete_claimed_scan(self):
        root = "/volume1/FLOWPILOT_G104_SYNTHETIC_TEST/project"
        observations = (
            seen("handoff/summary.md", "synthetic://g104/summary"),
            seen("design/architecture.md", "synthetic://g104/architecture"),
        )
        kwargs = dict(request="handoff audit", root=root, required_paths=(
            "handoff/summary.md", "design/architecture.md", "handoff/signoff.md",
        ), metadata_approved=True, unknown_processing_accepted=True)
        complete = ObservationBatch(root, observations, True, True, True, True)
        partial = ObservationBatch(root, observations, True, True, False, False)
        good = evaluate_offline(**kwargs, batch=complete)
        uncertain = evaluate_offline(**kwargs, batch=partial)
        self.assertEqual(good.status, "BLOCKED")
        self.assertEqual([x.state for x in good.report.items],
                         [ItemState.PRESENT, ItemState.PRESENT, ItemState.MISSING])
        self.assertEqual(uncertain.status, "NEEDS_REVIEW")
        self.assertTrue(all(x.state is ItemState.NOT_CHECKED for x in uncertain.report.items))
        self.assertFalse(good.actual_nas_verified)

    def test_no_metadata_approval(self):
        x=evaluate_offline(**{**BASE,'metadata_approved':False},batch=fixture())
        self.assertEqual(x.status,'WAITING_APPROVAL');self.assertIsNone(x.report)

    def test_no_claimed_processing_consent(self):
        x=evaluate_offline(**{**BASE,'unknown_processing_accepted':False},batch=fixture())
        self.assertEqual(x.status,'WAITING_APPROVAL')

    def test_no_runtime_adapter_no_fake_results(self):
        x=evaluate_offline(**BASE)
        self.assertEqual(x.status,'NEEDS_REVIEW');self.assertIn('NO_OBSERVED_METADATA',x.limitations)

    def test_string_document_approval_never_unlocks_pipeline_stage(self):
        batch = fixture(seen('README.md', 'synthetic://a'),
                        seen('release/output.pdf', 'synthetic://b'))
        x = evaluate_offline(**{**BASE, 'request': 'summarize document'},
                             batch=batch, document_approved='true',
                             returned_document_refs=('synthetic://a',))
        self.assertEqual(x.status, 'NEEDS_REVIEW')
        self.assertNotIn('document', [s.id for s in x.plan.steps])

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
        x=evaluate_offline(**{**BASE,'request':'summarize document'},batch=fixture(seen('README.md','synthetic://a'),seen('release/output.pdf','synthetic://b')),document_approved=True,returned_document_refs=('synthetic://a',),
                           processing_destination_confirmed=True)
        self.assertEqual(x.status,'NEEDS_REVIEW');self.assertEqual([s.id for s in x.plan.steps],['inventory','document','report'])

    def test_writes_blocked_before_evidence(self):
        x=evaluate_offline(**{**BASE,'request':'파일 삭제해줘'},batch=fixture(seen('README.md','synthetic://a')))
        self.assertEqual(x.status,'BLOCKED');self.assertIsNone(x.report)

    def test_document_outside_required_checklist_is_blocked(self):
        batch=fixture(seen('README.md','synthetic://approved'),
                      seen('release/output.pdf','synthetic://output'),
                      seen('unselected/secret.txt','synthetic://unselected'))
        x=evaluate_offline(**{**BASE,'request':'summarize document'},batch=batch,
                           document_approved=True,
                           returned_document_refs=('synthetic://unselected',))
        self.assertEqual(x.status,'BLOCKED')
        self.assertNotIn('document',[s.id for s in x.plan.steps])

    def test_partial_inventory_blocks_document_stage(self):
        batch=fixture(seen('README.md','synthetic://a'),complete=False)
        x=evaluate_offline(**{**BASE,'request':'summarize document'},batch=batch,
                           document_approved=True,returned_document_refs=('synthetic://a',))
        self.assertEqual(x.status,'NEEDS_REVIEW')
        self.assertIn('DOCUMENT_STAGE_BLOCKED_UNVERIFIED_INVENTORY',x.limitations)
        self.assertNotIn('document',[s.id for s in x.plan.steps])

    def test_unverified_registered_agent_blocks_document_stage(self):
        batch=ObservationBatch(ROOT_DIR,(seen('README.md','synthetic://a'),),
                               permission_confirmed=True,registered_adapter_confirmed=False,
                               scan_complete=True,pagination_complete=True)
        x=evaluate_offline(**{**BASE,'request':'summarize document'},batch=batch,
                           document_approved=True,returned_document_refs=('synthetic://a',))
        self.assertEqual(x.status,'NEEDS_REVIEW')
        self.assertNotIn('document',[s.id for s in x.plan.steps])


    def test_untrusted_duplicate_selected_document_does_not_plan_content(self):
        batch = fixture(seen('README.md', 'synthetic://good'),
                        Observed('README.md', 'synthetic://symlink', is_symlink=True, contained=None),
                        seen('release/output.pdf', 'synthetic://pdf'))
        x = evaluate_offline(**{**BASE, 'request': 'summarize document'},
                             batch=batch, document_approved=True,
                             returned_document_refs=('synthetic://good',))
        self.assertEqual(x.status, 'NEEDS_REVIEW')
        self.assertEqual(x.report.items[0].state, ItemState.NOT_CHECKED)
        self.assertNotIn('document', [s.id for s in x.plan.steps])
        self.assertIn('DOCUMENT_STAGE_BLOCKED_UNVERIFIED_SELECTED_REFERENCE', x.limitations)

    def test_competing_version_selected_document_does_not_plan_content(self):
        batch = fixture(seen('README.md', 'synthetic://good'),
                        seen('README_v2.md', 'synthetic://other'),
                        seen('release/output.pdf', 'synthetic://pdf'))
        x = evaluate_offline(**{**BASE, 'request': 'summarize document'},
                             batch=batch, document_approved=True,
                             returned_document_refs=('synthetic://good',),
                             version_candidates={'README.md': ('README_v2.md',)})
        self.assertEqual(x.report.items[0].state, ItemState.VERSION_REVIEW)
        self.assertNotIn('document', [s.id for s in x.plan.steps])
        self.assertIn('DOCUMENT_STAGE_BLOCKED_UNVERIFIED_SELECTED_REFERENCE', x.limitations)

    def test_reused_reference_for_two_required_paths_does_not_plan_content(self):
        batch = fixture(seen('README.md', 'synthetic://shared'),
                        seen('release/output.pdf', 'synthetic://shared'))
        x = evaluate_offline(**{**BASE, 'request': 'summarize document'},
                             batch=batch, document_approved=True,
                             returned_document_refs=('synthetic://shared',))
        self.assertNotIn('document', [s.id for s in x.plan.steps])
        self.assertIn('DOCUMENT_STAGE_BLOCKED_UNVERIFIED_SELECTED_REFERENCE', x.limitations)

    def test_root_mismatch_removes_document_plan(self):
        batch = fixture(seen('README.md', 'synthetic://good'),
                        root='/volume1/projects/different')
        x = evaluate_offline(**{**BASE, 'request': 'summarize document'},
                             batch=batch, document_approved=True,
                             returned_document_refs=('synthetic://good',))
        self.assertEqual(x.status, 'BLOCKED')
        self.assertIn('ROOT_MISMATCH', x.limitations)
        self.assertNotIn('document', [s.id for s in x.plan.steps])

    def test_string_permission_cannot_enable_document_inventory(self):
        batch = ObservationBatch(ROOT_DIR, (seen('README.md', 'synthetic://good'),),
                                 permission_confirmed='true', registered_adapter_confirmed=True,
                                 scan_complete=True, pagination_complete=True)
        x = evaluate_offline(**{**BASE, 'request': 'summarize document'},
                             batch=batch, document_approved=True,
                             returned_document_refs=('synthetic://good',))
        self.assertEqual(x.status, 'NEEDS_REVIEW')
        self.assertIn('DOCUMENT_STAGE_BLOCKED_UNVERIFIED_INVENTORY', x.limitations)
        self.assertNotIn('document', [s.id for s in x.plan.steps])

if __name__=='__main__':unittest.main()
