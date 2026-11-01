"""G159 exact pair documentary agreement and attestation tests: synthetic only."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
from contextlib import redirect_stdout
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g159_claims_rights_gate as g159


def texts():
    p = (
        "one folder confirm scope explicit, architect security builder QA not separate. "
        "subject to registration file-agent document-agent. DESIGN_ONLY no shell "
        "not simulated NAS execution. First-party Checker remain unverified, "
        "not Uliya runtime results. OpenAI ChatGPT no third-party code or models. "
        "Owner must confirm rights licenses."
    )
    s = (
        "Limit a run to one folder. Never infer consent. Architect: Security: "
        "Builder: QA: not four separately registered agents. Registered file-agent "
        "document-agent only if approved. DESIGN_ONLY NOT_EXECUTABLE_ON_CURRENT_CAPABILITIES. "
        "Not passed an independently executed first-party Uliya Checker, "
        "no native Expert permissions. AI tools and principal uses. "
        "Third-party components/open-source libraries included: none. "
        "Rights check still required before submission."
    )
    return p, s, ("flowpilot-3/SKILL.md", "flowpilot-3/references/A.md",
                  "flowpilot-3/references/B.md")


class G159ClaimsTests(TestCase):
    def test_valid_cross_referenced_draft_stays_hold(self):
        result = g159.compare_text(*texts())
        self.assertEqual(result["documentary_claims_cross_referenced"], 7)
        self.assertFalse(result["platform_license_approved"])
        self.assertFalse(result["originality_independently_verified"])
        self.assertEqual(result["release_gate"], "HOLD")

    def test_owner_originality_is_not_claimed_verified(self):
        result = g159.compare_text(*texts())
        self.assertIn("entrant_original_authorship_and_rights", result["owner_attestations_required"])
        self.assertIn("authentic_ugreen_creation_tool_and_first_party_checker",
                      result["external_verification_pending"])

    def test_missing_consent_proof_refused(self):
        p,s,names=texts()
        with self.assertRaisesRegex(g159.ClaimsRefused,"scope_and_consent"):
            g159.compare_text(p,s.replace("Never infer consent","assume consent"),names)

    def test_four_reviews_cannot_be_separate_registered_experts(self):
        p,s,names=texts()
        with self.assertRaisesRegex(g159.ClaimsRefused,"four_internal_review_perspectives"):
            g159.compare_text(p,s.replace("not four separately registered agents","four separate agents"),names)

    def test_tool_capability_must_be_conditional(self):
        p,s,names=texts()
        with self.assertRaisesRegex(g159.ClaimsRefused,"conditional_registered_experts"):
            g159.compare_text(p.replace("subject to registration","fully installed"),s,names)

    def test_unverified_checker_status_must_be_disclosed(self):
        p,s,names=texts()
        with self.assertRaisesRegex(g159.ClaimsRefused,"honest_unverified_runtime_status"):
            g159.compare_text(p.replace("remain unverified","already passed"),s,names)

    def test_ai_assistance_disclosure_required(self):
        p,s,names=texts()
        with self.assertRaisesRegex(g159.ClaimsRefused,"ai_and_third_party_disclosure"):
            g159.compare_text(p.replace("OpenAI ChatGPT","undisclosed"),s,names)

    def test_no_binary_as_initial_skill(self):
        p,s,names=texts()
        with self.assertRaisesRegex(g159.ClaimsRefused,"MARKDOWN_ONLY"):
            g159.compare_text(p,s,names+("flowpilot-3/run.sh",))

    def test_empty_content_fails_closed(self):
        _,s,names=texts()
        with self.assertRaisesRegex(g159.ClaimsRefused,"EMPTY_TEXT"):
            g159.compare_text("",s,names)

    def test_empty_raw_pair_refused_without_network(self):
        with self.assertRaisesRegex(g159.ClaimsRefused,"PACKAGE_INPUT_INVALID"):
            g159.review_package(b"")

    def test_bad_private_file_path_redacted(self):
        out=io.StringIO()
        with redirect_stdout(out):
            code=g159.main(["--review-package","/owner/private-sensitive.pdf"])
        self.assertEqual(code,2)
        self.assertNotIn("private-sensitive",out.getvalue())
        self.assertEqual(json.loads(out.getvalue())["release_gate"],"HOLD")


if __name__ == "__main__":
    main()
