"""G256 ensures exact private candidate binding; no private artifacts are CI fixtures."""
from __future__ import annotations

import io
import json
from pathlib import Path
import stat
import sys
import unittest
from zipfile import ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g256_candidate_admission as g256


def archive(members: dict, *, duplicate: bool = False, symlink: bool = False) -> bytes:
    raw=io.BytesIO()
    with ZipFile(raw,"w") as z:
        for name, payload in members.items():
            info=ZipInfo(name)
            if symlink and name.endswith("SKILL.md"):
                info.create_system=3
                info.external_attr=(stat.S_IFLNK | 0o777) << 16
            z.writestr(info,payload)
        if duplicate:
            z.writestr(next(iter(members)),b"EXTRA")
    return raw.getvalue()


def fixtures():
    parent=("---\nname: flowpilot-3\ndescription: test\n---\n"
            + "\n".join(g256.MODES)
            + "\nDESIGN_ONLY / NOT_EXECUTED\n"
            + "\n".join(sorted(g256.MEMBERS - {"flowpilot-3/SKILL.md"})))
    members={name: b"reference test" for name in g256.MEMBERS}
    members["flowpilot-3/SKILL.md"]=parent.encode()
    members["flowpilot-3/references/workflow-council-and-repair.md"]=(
        b"Architect Security Builder QA Maximum one bounded correction")
    skill=archive(members)
    kit=archive({"uliya-skill-kit/scripts/check-skill.mjs":b"mock-only, NEVER execute"})
    pdf=b"%PDF-1.4\nfake PDF TEST DATA"
    audit_record={
       "status":"ALTERNATIVE_VERIFIED_LOCALLY_NOT_ADOPTED_NOT_SUBMITTED",
       "skill_zip":{"sha256":g256.sha(skill)},
       "pdf":{"sha256":g256.sha(pdf)},
       "independent_checks":{"passed":24,"failed":0},
       "first_party_uliya_checker":{"status":"static-pass","exit_code":0},
       "creator_provenance":"NOT_VERIFIED",
       "runtime_registered_agents":"NOT_RUN",
       "owner_final_release_approved":False,
       "official_submission":"NOT_SUBMITTED","release_gate":"HOLD"}
    audit=json.dumps(audit_record).encode()
    d={"skill":skill,"kit":kit,"pdf":pdf,"audit":audit}
    return d,{k:g256.sha(v) for k,v in d.items()}


class G256AdmissionTests(unittest.TestCase):
    def test_valid_local_chain_never_claims_vendor_runtime(self):
        d,pins=fixtures()
        result=g256.verify_bytes(**d,expected=pins)
        self.assertEqual(result["status"],"EXACT_G226_SOURCE_PDF_AND_HISTORY_BOUND_LOCAL_ONLY")
        self.assertFalse(result["checker_executed_by_this_verifier"])
        self.assertFalse(result["official_creator_provenance_verified"])
        self.assertFalse(result["nas_verified"])
        self.assertFalse(result["devpost_submitted"])

    def test_every_exact_file_byte_is_pinned(self):
        d,pins=fixtures()
        for key in d:
            bad=dict(d);bad[key]+=b"x"
            with self.subTest(key=key),self.assertRaises(g256.AdmissionRefused):
                g256.verify_bytes(**bad,expected=pins)

    def test_record_cannot_overclaim_creator_or_release(self):
        d,_=fixtures()
        for key,value in (("creator_provenance","VERIFIED"),
                          ("owner_final_release_approved",True),
                          ("official_submission","SUBMITTED")):
            bad=dict(d);record=json.loads(d["audit"]);record[key]=value
            bad["audit"]=json.dumps(record).encode()
            pins={k:g256.sha(v) for k,v in bad.items()}
            with self.subTest(field=key),self.assertRaises(g256.AdmissionRefused):
                g256.verify_bytes(**bad,expected=pins)

    def test_new_zip_includes_rogue_file_or_symlink(self):
        d,_=fixtures()
        original=archive({"flowpilot-3/SKILL.md":b"oops",
                          "flowpilot-3/evil.py":b"print('no')"})
        bad=dict(d);bad["skill"]=original
        pins={k:g256.sha(v) for k,v in bad.items()}
        with self.assertRaises(g256.AdmissionRefused):
            g256.verify_bytes(**bad,expected=pins)

    def test_fake_checker_result_refused(self):
        d,_=fixtures()
        record=json.loads(d["audit"]);record["first_party_uliya_checker"]["status"]="not-uploadable"
        d["audit"]=json.dumps(record).encode()
        pins={k:g256.sha(v) for k,v in d.items()}
        with self.assertRaises(g256.AdmissionRefused):
            g256.verify_bytes(**d,expected=pins)

    def test_private_file_only_main_needs_all_args(self):
        with self.assertRaises(SystemExit) as caught:
            g256.main([])
        self.assertEqual(caught.exception.code,2)


if __name__ == "__main__":
    unittest.main()
