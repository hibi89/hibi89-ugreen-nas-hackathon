"""G258 executable current-Skill check; PUBLIC repo contains synthetic only."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from test_sdk_parameter_matrix import fake
import flowpilot_g258_skill_dispatch_binding as g258
import flowpilot_g257_native_trial_matrix as g257


def sample_source():
    tick=chr(96)
    main="""---
name: flowpilot-3
description: code-owned synthetic only
---

# Goal
CHECK_DELIVERY REVIEW_VERSIONS REVIEW_DOCUMENT DESIGN_WORKFLOW PLAN_ONLY

# Required input
Owner separately approves content access, metadata and exact root.

# Orchestration
Read references/modes-and-evidence.md, references/failure-and-disclosure.md
and references/workflow-council-and-repair.md.
ug-filesystem ug-document
"""
    main+=" ".join(tick+x+tick for x in
        ("ls","find","stat","sha256sum","metadata","qa","extract","reconcile"))
    main+="\nPLAN_ONLY / NOT_CHECKED\nDESIGN_ONLY / NOT_EXECUTED\n"
    main+=("\n"+tick+"delegate --target file-agent --instruction "
           "'First verify this instruction contains current-session owner metadata approval and never acts without authorization, without following symlinks.'"+tick)
    main+="\nThe owner separately approves content access to real exact document references.\n"
    main+=("\n"+tick+"delegate --target document-agent --instruction "
           "'First verify real document references and separate explicit owner consent for each reference. Do not search other files.'"+tick)
    main+="\n# Completion and failure\n"
    main+="\n".join("- "+tick+s+tick+": stop unless valid" for s in
        ("completed","failed","cancelled","waiting_user","waiting_approval"))
    return main


def build_skill(main=None, extra=None):
    docs={
        "flowpilot-3/SKILL.md":sample_source() if main is None else main,
        "flowpilot-3/references/modes-and-evidence.md":"read-only",
        "flowpilot-3/references/failure-and-disclosure.md":"fail closed",
        "flowpilot-3/references/workflow-council-and-repair.md":
            "Architect Security Builder QA Maximum one bounded correction",
    }
    if extra: docs.update(extra)
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        for p,s in docs.items():z.writestr(p,s)
    return out.getvalue()


def inputs(main=None,extra=None):
    skill=build_skill(main,extra)
    kit,digest=fake()
    return skill,kit,hashlib.sha256(skill).hexdigest(),digest


class G258ExactSkillPolicyTests(unittest.TestCase):
    def test_current_skill_dual_guarded_agents_only(self):
        skill,kit,s,k=inputs()
        result=g258.verify_current_skill(skill,kit,skill_pin=s,kit_pin=k,
                                         synthetic_only=True)
        self.assertEqual(result["read_only_catalog_actions_rechecked"],8)
        self.assertEqual(result["registered_expert_targets_claimed_only"],
                         ["file-agent","document-agent"])
        self.assertEqual(len(result["guarded_instruction_sha256"]),2)
        self.assertFalse(result["executable_command_generated"])
        self.assertFalse(result["nas_verified"])

    def test_unauthorized_real_pin_override_and_stale_skill(self):
        skill,kit,s,k=inputs()
        with self.assertRaises(g258.SkillBoundaryRefused):
            g258.verify_current_skill(skill,kit,skill_pin=s,kit_pin=k)
        for p,b in ((skill+b"x",kit),(skill,kit+b"x")):
            with self.assertRaises(g258.SkillBoundaryRefused):
                g258.verify_current_skill(p,b,skill_pin=s,kit_pin=k,
                                           synthetic_only=True)

    def test_malicious_skill_mutations_fail_closed(self):
        before=sample_source()
        variants=[
            before.replace("file-agent","shell-agent"),
            before.replace("PLAN_ONLY / NOT_CHECKED","PLAN_ONLY / RUN"),
            before.replace("DESIGN_ONLY / NOT_EXECUTED","DESIGN_ONLY / EXECUTED"),
            before.replace("current-session owner metadata approval","implicit approval"),
            before.replace("without following symlinks","follow all symlinks"),
            before.replace("real exact document references","guessed references"),
            before.replace("separate explicit owner consent for each reference","old consent"),
            before.replace("Do not search other files","Search all files"),
            before.replace(chr(96)+"find"+chr(96),chr(96)+"del"+chr(96)),
            before+"\n"+chr(96)+"delegate --target extra-agent --instruction 'run'"+chr(96),
            before+"\n"+chr(96)*3+"bash\nrm -rf /\n"+chr(96)*3,
        ]
        for value in variants:
            with self.subTest(change=value[-32:]):
                skill,kit,s,k=inputs(value)
                with self.assertRaises(g258.SkillBoundaryRefused):
                    g258.verify_current_skill(skill,kit,skill_pin=s,
                                              kit_pin=k,synthetic_only=True)

    def test_unexpected_member_blocks_private_source(self):
        skill,kit,s,k=inputs(extra={"flowpilot-3/script.py":"print('bad')"})
        with self.assertRaises(g258.SkillBoundaryRefused):
            g258.verify_current_skill(skill,kit,skill_pin=s,kit_pin=k,
                                      synthetic_only=True)

    def test_g257_rechecks_current_bytes_instead_of_reused_receipt(self):
        skill,kit,s,k=inputs()
        bare=g257.prepare_trial(kit,{},test_sha=k)
        self.assertFalse(bare["current_skill_rechecked"])
        bound=g257.prepare_trial(kit,{},test_sha=k,candidate_skill=skill,
                                  test_candidate_sha=s)
        self.assertTrue(bound["current_skill_rechecked"])
        self.assertEqual(len(bound["current_skill_instruction_sha256"]),2)
        self.assertFalse(bound["nas_verified"])
        self.assertFalse(bound["may_activate_nas_trial"])
        self.assertEqual(sum(x["maximum_minutes"] for x in bound["scenarios"]),180)
        with self.assertRaises(g257.TrialReadinessRefused):
            g257.prepare_trial(kit,{},test_sha=k,candidate_skill=skill+b"x",
                               test_candidate_sha=s)
        with self.assertRaises(g257.TrialReadinessRefused):
            g257.prepare_trial(kit,{},test_sha=k,candidate_skill=skill)

    def test_forged_write_effect_cannot_pass_as_read(self):
        skill,_,s,_=inputs()
        def change(c):
            for action in c["clis"][0]["actions"]:
                if action["name"] == "find":
                    action["effect"] = "state-change"
        kit,k=fake(change)
        with self.assertRaises(g258.SkillBoundaryRefused):
            g258.verify_current_skill(skill,kit,skill_pin=s,kit_pin=k,
                                      synthetic_only=True)


if __name__=="__main__":
    unittest.main()
