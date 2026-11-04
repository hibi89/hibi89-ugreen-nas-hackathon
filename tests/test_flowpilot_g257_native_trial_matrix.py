"""G257 offline-only operational readiness and trial evidence fail-closed tests."""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from test_sdk_parameter_matrix import fake
import flowpilot_g257_native_trial_matrix as g257


def proof():
    return {
        "schema":g257.G256_SCHEMA, "status":g257.G256_STATUS,
        "candidate_skill_zip_sha256":g257.G226_SHA,
        "candidate_pdf_sha256":g257.G226_PDF,"kit_sha256":g257.KIT_SHA,
        "recorded_official_checker_static_pass":True,
        "checker_executed_by_this_verifier":False,
        "official_creator_provenance_verified":False,"nas_verified":False,
        "participant_release_approved":False,"devpost_submitted":False,
        "release_gate":"HOLD",
    }


class G257TrialPreparationTests(unittest.TestCase):
    def test_bad_official_kit_is_rejected_before_catalog(self):
        with patch.object(g257,"matrix",
                          side_effect=AssertionError("unexpected parser")):
            with self.assertRaises(g257.TrialReadinessRefused):
                g257.prepare_trial(b"not official",proof())

    def test_synthetic_fixture_matrix_fails_to_claim_live_rights(self):
        data, digest=fake()
        result=g257.prepare_trial(data,proof(),test_sha=digest)
        self.assertEqual(result["status"],"SYNTHETIC_TRIAL_PLAN_ONLY")
        self.assertEqual(sum(x["maximum_minutes"] for x in result["scenarios"]),180)
        self.assertEqual(len(result["scenarios"]),7)
        self.assertEqual(len(result["catalog_actions_checked"]),5)
        for key in ("nas_verified","exact_registered_expert_signatures_verified",
                    "native_return_envelope_verified","performs_native_cli_calls",
                    "starts_trial_or_timer","owner_explicit_live_authorization_received"):
            self.assertFalse(result[key])

    def test_actual_owner_admission_denies_all_overclaims(self):
        for field,value in (("nas_verified",True),("devpost_submitted",True),
                            ("participant_release_approved",True),
                            ("official_creator_provenance_verified",True),
                            ("candidate_skill_zip_sha256","f"*64)):
            invalid=proof();invalid[field]=value
            with self.subTest(field=field),self.assertRaises(g257.TrialReadinessRefused):
                g257._receipt_ok(invalid,g257.KIT_SHA)

    def test_trusted_kit_receipt_rejects_unknown_extra_keys(self):
        invalid=proof();invalid["server_token"]="never"
        with self.assertRaises(g257.TrialReadinessRefused):
            g257._receipt_ok(invalid,g257.KIT_SHA)

    def test_trial_note_is_never_credited_to_real_nas(self):
        data,digest=fake()
        packet=g257.prepare_trial(data,proof(),test_sha=digest)
        notes=[{"case_id":"REGISTRY_AND_RIGHTS","outcome":"OPERATOR_REPORTED",
                "trace_sha256":"a"*64,"reason_code":"NONE"}]
        result=g257.summarize_operator_notes(packet,notes)
        self.assertFalse(result["nas_verified"])
        self.assertEqual(result["status"],"REQUIRES_INDEPENDENT_REGISTERED_NAS_READBACK")
        self.assertEqual(result["owner_notes_received"],1)

    def test_forged_private_note_and_duplicate_refused(self):
        data,digest=fake()
        packet=g257.prepare_trial(data,proof(),test_sha=digest)
        original={"case_id":"REGISTRY_AND_RIGHTS","outcome":"OPERATOR_REPORTED",
                  "trace_sha256":None,"reason_code":"UNKNOWN_SIGNATURE"}
        for bad in [
            [original,original],
            [{**original,"scope":"/volume1/owner/private"}],
            [{**original,"outcome":"PASSED_NATIVE"}],
            [{**original,"trace_sha256":"KEYS_SECRET"}],
            [{**original,"reason_code":"full owner path"}],
        ]:
            with self.subTest(bad=str(bad)[:60]), self.assertRaises(g257.TrialReadinessRefused):
                g257.summarize_operator_notes(packet,bad)

    def test_invalid_stage_packet_rejected(self):
        data,digest=fake()
        packet=g257.prepare_trial(data,proof(),test_sha=digest)
        bad=copy.deepcopy(packet);bad["scenarios"][0]["id"]="DROP_ALL_FILES"
        with self.assertRaises(g257.TrialReadinessRefused):
            g257.summarize_operator_notes(bad,[])

    def test_duplicate_json_private_evidence_denied(self):
        with self.assertRaises(g257.TrialReadinessRefused):
            g257._strict_json(b'{"x":1,"x":2}')
        self.assertEqual(g257._strict_json(b'{"approved":false}'),{"approved":False})

    def test_no_owner_inputs_without_explicit_paths(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as c:
                g257.main([])
        self.assertEqual(c.exception.code,2)


if __name__=="__main__":
    unittest.main()
