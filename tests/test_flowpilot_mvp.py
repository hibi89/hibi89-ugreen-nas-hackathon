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
                       document_approved=True, returned_document_refs=("actual-reference-1",))
        self.assertEqual(tuple(s.id for s in p.steps), ("inventory", "document", "report"))

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
                       document_approved=True, returned_document_refs=("",))

    def test_markdown_source_no_scripts_or_real_nas_claim(self):
        skill = (ROOT / "skill" / "flowpilot-nas" / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: flowpilot-nas\n"))
        for clause in ("WAITING_USER", "NOT_CHECKED", "VERSION_REVIEW", "file-agent", "document-agent", "official Creator", "No writes"):
            # Capitalization is not significant for a declared policy.
            self.assertIn(clause.lower(), skill.lower())
        self.assertLess(len(skill.encode("utf-8")), 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
