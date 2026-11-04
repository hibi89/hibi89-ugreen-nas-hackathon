"""G265 operator-note source/replay protection; synthetic inputs only."""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g265_bound_operator_notes as g265


def plan():
    return {
        "schema": g265.PLAN_SCHEMA,
        "status": "CURRENT_SKILL_BOUND_OFFLINE_TRIAL_PLAN_READY",
        "source_candidate_sha256": g265.G226_SHA,
        "public_kit_sha256": g265.KIT_SHA,
        "current_skill_rechecked": True,
        "current_skill_instruction_sha256": ["a" * 64, "b" * 64],
        "starts_trial_or_timer": False,
        "performs_native_cli_calls": False,
        "may_activate_nas_trial": False,
        "exact_registered_expert_signatures_verified": False,
        "effective_nas_permissions_verified": False,
        "native_return_envelope_verified": False,
        "owner_explicit_live_authorization_received": False,
        "nas_verified": False,
        "official_creator_provenance_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
        "scenarios": [
            {"id": s, "status": "NOT_RUN", "effective_permissions_verified": False,
             "required_independent_live_evidence": True}
            for s in g265.STAGE_IDS
        ],
        "operator_scope": {
            "schema": g265.SCOPE_SCHEMA,
            "status": "LOCAL_SCOPE_REQUEST_BOUND_AWAITING_REAL_EXPERT",
            "request_sha256": "c" * 64,
            "required_file_count": 2,
            "owner_paths_exposed": False,
            "consent_independently_verified": False,
            "actual_native_instruction_created": False,
        },
    }


def notes(source=None):
    source = source or plan()
    return {"schema": g265.SCHEMA,
            "plan_sha256": g265.plan_identity(source)["plan_sha256"],
            "scope_sha256": source["operator_scope"]["request_sha256"],
            "notes": [{"case_id": "REQUIRED_FILES", "outcome": "OPERATOR_REPORTED",
                       "trace_sha256": "d" * 64, "reason_code": "NONE"}]}


class SourceBoundOperatorTests(unittest.TestCase):
    def test_source_bound_report_never_proves_nas(self):
        out = g265.bind_operator_notes(plan(), notes())
        self.assertFalse(out["nas_verified"])
        self.assertFalse(out["registered_expert_invocation_verified"])
        self.assertFalse(out["operator_claims_are_signed_vendor_evidence"])
        self.assertEqual(out["note_count"], 1)
        self.assertEqual(out["outcome_counts"]["OPERATOR_REPORTED"], 1)
        self.assertNotIn("/volume", json.dumps(out))

    def test_deterministic_redacted_digest(self):
        self.assertEqual(g265.bind_operator_notes(plan(), notes()),
                         g265.bind_operator_notes(plan(), notes()))

    def test_stale_plan_fails_even_with_matching_scope(self):
        p = plan(); packet = notes(p)
        p["scenarios"][0]["maximum_minutes"] = 99
        with self.assertRaises(g265.OperatorNotesRefused):
            g265.bind_operator_notes(p, packet)

    def test_scope_swap_fails_even_with_same_trial(self):
        p = plan(); packet = notes(p)
        p["operator_scope"]["request_sha256"] = "f" * 64
        with self.assertRaises(g265.OperatorNotesRefused):
            g265.bind_operator_notes(p, packet)

    def test_missing_scope_denied(self):
        p = plan(); p.pop("operator_scope")
        with self.assertRaises(g265.OperatorNotesRefused):
            g265.plan_identity(p)

    def test_source_and_runtime_overclaim_denied(self):
        for key, value in (("public_kit_sha256", "1" * 64),
                           ("source_candidate_sha256", "2" * 64),
                           ("nas_verified", True),
                           ("effective_nas_permissions_verified", True),
                           ("owner_explicit_live_authorization_received", True),
                           ("official_creator_provenance_verified", True),
                           ("devpost_submitted", True)):
            p = plan(); p[key] = value
            with self.subTest(key=key), self.assertRaises(g265.OperatorNotesRefused):
                g265.plan_identity(p)

    def test_duplicate_case_and_extra_private_field_rejected(self):
        for changed in (lambda x: x["notes"].append(copy.deepcopy(x["notes"][0])),
                        lambda x: x["notes"][0].update(path="/owner/private"),
                        lambda x: x["notes"][0].update(outcome="PASSED_NATIVE"),
                        lambda x: x["notes"][0].update(reason_code="owner full path")):
            p = plan(); packet = notes(p); changed(packet)
            with self.assertRaises(g265.OperatorNotesRefused):
                g265.bind_operator_notes(p, packet)

    def test_empty_report_cannot_claim_nas(self):
        p = plan(); packet = notes(p); packet["notes"] = []
        report = g265.bind_operator_notes(p, packet)
        self.assertEqual(report["note_count"], 0)
        self.assertFalse(report["nas_verified"])

    def test_private_fields_in_plan_rejected(self):
        p = plan(); p["operator_scope"]["root"] = "/volume1/private"
        with self.assertRaises(g265.OperatorNotesRefused):
            g265.bind_operator_notes(p, notes())

    def test_cli_valid_json_exit_zero_offline_only(self):
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t); p = plan(); packet = notes(p)
            a, b = folder / "plan.json", folder / "notes.json"
            a.write_text(json.dumps(p)); b.write_text(json.dumps(packet))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = g265.main(["--plan", str(a), "--notes", str(b)])
            self.assertEqual(result, 0)
            body = json.loads(stdout.getvalue())
            self.assertFalse(body["nas_verified"])
            self.assertNotIn("/owner/private", stdout.getvalue())

    def test_cli_duplicate_json_refused_without_leak(self):
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t); a, b = folder / "p.json", folder / "n.json"
            a.write_text('{"schema":1,"schema":2,"private":"/owner"}')
            b.write_text('{}')
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = g265.main(["--plan", str(a), "--notes", str(b)])
            self.assertEqual(result, 2)
            self.assertNotIn("/owner", stdout.getvalue())

    def test_invalid_runtime_scenario_denied(self):
        p = plan(); p["scenarios"][3]["status"] = "completed"
        with self.assertRaises(g265.OperatorNotesRefused):
            g265.plan_identity(p)


if __name__ == "__main__":
    unittest.main()
