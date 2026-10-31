"""FlowPilot G43 offline prototype tests: NOT official Uliya/NAS execution."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from flowpilot.planner import draft_plan, State, Intent

P = dict(request="Check project handoff deliverables", root="/volume1/projects/alpha",
         required_paths=("README.md", "release/output.pdf"),
         metadata_approved=True, unknown_processing_accepted=True)


class FlowPilotMVP(unittest.TestCase):
    def test_three_missing_slots(self):
        p = draft_plan("check missing files")
        self.assertEqual(p.state, State.WAITING_USER)
        self.assertEqual(len(p.questions), 2)

    def test_empty_goal_asks_clarification(self):
        self.assertEqual(draft_plan("").state, State.WAITING_USER)

    def test_unsupported_intent_does_not_execute(self):
        self.assertEqual(draft_plan("build arbitrary workflow", **{k: v for k, v in P.items() if k != "request"}).state, State.WAITING_USER)

    def test_required_consent_not_inferred(self):
        args = dict(P); args["metadata_approved"] = False
        p = draft_plan(**args)
        self.assertEqual(p.state, State.WAITING_APPROVAL)
        self.assertEqual(len(p.steps), 0)

    def test_unknown_processing_location_consent(self):
        args = dict(P); args["unknown_processing_accepted"] = False
        self.assertEqual(draft_plan(**args).state, State.WAITING_APPROVAL)

    def test_handoff_plan_is_nonexecuting_and_bounded(self):
        p = draft_plan(**P)
        self.assertEqual(p.intent, Intent.HANDOFF_AUDIT)
        self.assertEqual(p.state, State.READY_FOR_ADAPTER_CHECK)
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "versions", "report"))
        self.assertFalse(p.did_access_nas)

    def test_check_only_has_no_extra_expert(self):
        p = draft_plan(**{**P, "request": "check required files"})
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "report"))

    def test_review_variants(self):
        p = draft_plan(**{**P, "request": "compare versions"})
        self.assertEqual(p.intent, Intent.REVIEW_VERSIONS)
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "versions", "report"))

    def test_summary_needs_separate_document_consent(self):
        p = draft_plan(**{**P, "request": "summarize document"})
        self.assertNotIn("document", (s.id for s in p.steps))
        self.assertTrue(p.questions)
        self.assertIn("DOCUMENT_STAGE_WAITING_SEPARATE_APPROVAL_AND_REAL_FILE_REFS", p.limitations)

    def test_summary_only_exact_selected_refs(self):
        p = draft_plan(**{**P, "request": "summarize document"},
                       document_approved=True, returned_document_refs=("actual-reference-1",),
                       processing_destination_confirmed=True)
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "document", "report"))

    def test_g104_explicit_summary_of_handoff_document_preserves_document_consent(self):
        args = {**P, "request": "summarize handoff/summary.md"}
        pending = draft_plan(**args)
        self.assertEqual(pending.intent, Intent.SUMMARIZE_SELECTED)
        self.assertNotIn("document", (s.id for s in pending.steps))
        self.assertIn("DOCUMENT_STAGE_WAITING_SEPARATE_APPROVAL_AND_REAL_FILE_REFS", pending.limitations)
        approved = draft_plan(**args, document_approved=True,
                             returned_document_refs=("synthetic://g104/summary",),
                             processing_destination_confirmed=True)
        self.assertEqual(tuple(s.id for s in approved.steps), ("inventory", "document", "report"))
        self.assertFalse(approved.did_access_nas)

    def test_g104_explicit_version_comparison_is_not_shadowed_by_handoff(self):
        args = {**P, "request": "compare versions of handoff review drafts"}
        p = draft_plan(**args)
        self.assertEqual(p.intent, Intent.REVIEW_VERSIONS)
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "versions", "report"))

    def test_g104_explicit_required_check_not_shadowed_by_document_name(self):
        args = {**P, "request": "check required handoff/summary.md"}
        p = draft_plan(**args)
        self.assertEqual(p.intent, Intent.CHECK_REQUIRED)
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "report"))

    def test_g104_korean_explicit_summary_not_shadowed_by_handoff(self):
        args = {**P, "request": "납품 인계 문서를 요약해줘"}
        p = draft_plan(**args)
        self.assertEqual(p.intent, Intent.SUMMARIZE_SELECTED)
        self.assertNotIn("document", (s.id for s in p.steps))

    def test_g104_general_handoff_audit_still_works(self):
        args = {**P, "request": "audit handoff including version disagreements"}
        p = draft_plan(**args)
        self.assertEqual(p.intent, Intent.HANDOFF_AUDIT)

    def test_g108_filename_summarize_does_not_turn_check_into_content_read(self):
        args = {**P, "request": "check required handoff/summarize.md"}
        p = draft_plan(**args, document_approved=True,
                       returned_document_refs=("synthetic://content",))
        self.assertEqual(p.intent, Intent.CHECK_REQUIRED)
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "report"))

    def test_g108_summary_named_file_does_not_shadow_version_comparison(self):
        p = draft_plan(**{**P, "request": "compare versions of handoff/summarize.md"})
        self.assertEqual(p.intent, Intent.REVIEW_VERSIONS)
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "versions", "report"))

    def test_g108_korean_filename_not_mistaken_for_summary_command(self):
        p = draft_plan(**{**P, "request": "필수 파일 확인: handoff/요약해.md"})
        self.assertEqual(p.intent, Intent.CHECK_REQUIRED)
        self.assertNotIn("document", (s.id for s in p.steps))

    def test_g108_explicit_summary_commands_still_require_document_consent(self):
        for request in ("summarize handoff/summary.md",
                        "summarise handoff/summary.md", "납품 문서를 요약해주세요"):
            with self.subTest(request=request):
                p = draft_plan(**{**P, "request": request})
                self.assertEqual(p.intent, Intent.SUMMARIZE_SELECTED)
                self.assertNotIn("document", (s.id for s in p.steps))

    def test_denies_mutations_even_if_approved(self):
        for request in ("delete files", "move delivery", "업로드 전송"):
            with self.subTest(request=request):
                self.assertEqual(draft_plan(**{**P, "request": request}).state, State.BLOCKED)

    def test_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            draft_plan(**{**P, "required_paths": ("../.env",)})

    def test_rejects_sensitive_path(self):
        for path in ("release/.env", "docs/id_rsa", "config.json", ".ssh/known_hosts"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    draft_plan(**{**P, "required_paths": (path,)})

    def test_rejects_alias_and_scope_escape(self):
        for path in ("a\\b", "/absolute", "x//y", "x/./y", "x/../y"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    draft_plan(**{**P, "required_paths": (path,)})

    def test_rejects_unscoped_root(self):
        with self.assertRaises(ValueError):
            draft_plan(**{**P, "root": "/"})

    def test_rejects_duplicate_checklist(self):
        with self.assertRaises(ValueError):
            draft_plan(**{**P, "required_paths": ("a.pdf", "a.pdf")})

    def test_invalid_document_ref_is_not_trusted(self):
        with self.assertRaises(ValueError):
            draft_plan(**{**P, "request": "summarize document"},
                       document_approved=True, returned_document_refs=("",),
                       processing_destination_confirmed=True)

    def test_untrusted_string_metadata_approval_does_not_unlock_plan(self):
        x = draft_plan(**{**P, "metadata_approved": "true"})
        self.assertEqual(x.state, State.WAITING_APPROVAL)
        self.assertEqual(x.steps, ())

    def test_untrusted_integer_processing_approval_does_not_unlock_plan(self):
        x = draft_plan(**{**P, "unknown_processing_accepted": 1})
        self.assertEqual(x.state, State.WAITING_APPROVAL)
        self.assertEqual(x.steps, ())

    def test_untrusted_string_content_consent_does_not_plan_document(self):
        x = draft_plan(**{**P, "request": "summarize document"},
                       document_approved="yes",
                       returned_document_refs=("synthetic://a",))
        self.assertEqual(x.state, State.READY_FOR_ADAPTER_CHECK)
        self.assertNotIn("document", [s.id for s in x.steps])

    def test_g109_unknown_processing_metadata_consent_cannot_plan_content(self):
        p = draft_plan(**{**P, "request": "summarize handoff/summary.md"},
                       document_approved=True,
                       returned_document_refs=("synthetic://g104/summary",))
        self.assertEqual(p.intent, Intent.SUMMARIZE_SELECTED)
        self.assertNotIn("document", [s.id for s in p.steps])
        self.assertIn("DOCUMENT_PROCESSING_DESTINATION_UNVERIFIED", p.limitations)

    def test_g109_destination_string_claim_cannot_plan_content(self):
        p = draft_plan(**{**P, "request": "summarize handoff/summary.md"},
                       document_approved=True,
                       returned_document_refs=("synthetic://g104/summary",),
                       processing_destination_confirmed="true")
        self.assertNotIn("document", [s.id for s in p.steps])

    def test_markdown_source_no_scripts_or_real_nas_claim(self):
        skill = (ROOT / "skill" / "flowpilot-nas" / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: flowpilot-nas\n"))
        for clause in ("WAITING_USER", "NOT_CHECKED", "VERSION_REVIEW", "file-agent", "document-agent", "official Creator", "No writes"):
            # Capitalization is not significant for a declared policy.
            self.assertIn(clause.lower(), skill.lower())
        self.assertLess(len(skill.encode("utf-8")), 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
