"""G42: independent synthetic adversarial tests; NOT NAS security certification."""
import hashlib,io,json,stat,sys,unittest,zipfile
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from projectready.presence import FileEvidence,EvidenceOrigin,ScanEnvelope,check_presence
from projectready.policy_guard import Policy,Action,Result,assess
from projectready.version_candidates import detect_version_candidates,VersionSignal
from projectready.readiness import Requirement,ScanStatus,Verdict
R=(Requirement("a","delivery/a.pdf"),)
def snap(*paths):
    return ScanEnvelope(authorized_root_ref="SYNTHETIC",scope_prefix="delivery",
       status=ScanStatus.COMPLETE,evidence_origin=EvidenceOrigin.SDK_VERIFIED,
       adapter_verified=True,permission_granted=True,pagination_exhausted=True,
       complete_scope=True,scan_reference="synthetic://scan",
       observations=tuple(FileEvidence(p,"synthetic://"+str(i)) for i,p in enumerate(paths)))
class G42Adversarial(unittest.TestCase):
    def verdict(self,s):return check_presence(R,s).checks[0].verdict
    def test_synthetic_full_present(self):self.assertEqual(self.verdict(snap("delivery/a.pdf")),Verdict.PASS)
    def test_complete_missing(self):self.assertEqual(self.verdict(snap()),Verdict.FAIL)
    def test_partial_missing_unknown(self):self.assertEqual(self.verdict(replace(snap(),status=ScanStatus.PARTIAL)),Verdict.NOT_CHECKED)
    def test_denied_even_with_name_unknown(self):self.assertEqual(self.verdict(replace(snap("delivery/a.pdf"),status=ScanStatus.DENIED)),Verdict.NOT_CHECKED)
    def test_truncated_does_not_prove_missing(self):self.assertEqual(self.verdict(replace(snap(),pagination_exhausted=False)),Verdict.NOT_CHECKED)
    def test_no_consent(self):self.assertEqual(self.verdict(replace(snap("delivery/a.pdf"),permission_granted=False)),Verdict.NOT_CHECKED)
    def test_unverified_adapter(self):self.assertEqual(self.verdict(replace(snap("delivery/a.pdf"),adapter_verified=False)),Verdict.NOT_CHECKED)
    def test_empty_source_reference(self):self.assertEqual(self.verdict(replace(snap(),observations=(FileEvidence("delivery/a.pdf",""),))),Verdict.NOT_CHECKED)
    def test_duplicate_ambiguous(self):
        o=snap("delivery/a.pdf")
        self.assertEqual(self.verdict(replace(o,observations=o.observations*2)),Verdict.REVIEW)
    def test_outside_prefix_refused(self):
        with self.assertRaises(ValueError):check_presence((Requirement("bad","delivery-private/a"),),snap())
    def test_parent_traversal_refused(self):
        with self.assertRaises(ValueError):check_presence((Requirement("bad","delivery/../secret"),),snap())
    def test_backslash_refused(self):
        with self.assertRaises(ValueError):check_presence((Requirement("bad","delivery\\secret"),),snap())
    def test_outside_observation_refused(self):
        with self.assertRaises(ValueError):self.verdict(replace(snap(),observations=(FileEvidence("secret/token","synthetic://x"),)))
    def test_write_transfer_forbidden(self):
        policy=Policy(True,True,True,True)
        for a in (Action.CHANGE,Action.TRANSFER):
            with self.subTest(action=a):self.assertEqual(assess(a,policy).decision,Result.BLOCKED)
    def test_read_needs_separate_consent(self):
        self.assertEqual(assess(Action.READ,Policy(True,True,False,True)).decision,Result.BLOCKED)
    def test_versions_not_authoritative(self):
        v=detect_version_candidates(R[0],snap("delivery/a.pdf","delivery/a_v2.pdf"))
        self.assertEqual(v.signal,VersionSignal.CANDIDATES_REVIEW)
        self.assertFalse(v.authoritatively_verified_current_version)
    def test_g36_original_bytes_frozen(self):
        raw=(ROOT/"docs/submission/checker_inputs/G36_20261026/projectready-nas/SKILL.md").read_bytes()
        self.assertEqual(len(raw),14522)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),"e4e45dea7f2ca22a37c2c3803ed12d6b9914c7ca4686d9b891976ba1481610a4")
    def test_original_receipt_sha_pins_only(self):
        e=json.loads((ROOT/"docs/submission/evidence/G37_G36_EXACT_ARTIFACT_AUDIT_20261026.json").read_text())
        self.assertEqual(e["workflow"]["artifact_id"],12644844524)
        self.assertEqual(e["pdf"]["sha256"],"d5d1bf9383d9f7d811f2e8f30b649a41e2b2b382ce3d8ae4f60c75e917874936")
        self.assertEqual(e["zip"]["sha256"],"b3efbe261dc0ea35e90c290e362fc0efad70e59315d8cc5f0a009d445ece66d7")
        self.assertEqual(e["limitations"]["devpost"],"NOT_SUBMITTED")
    def test_synthetic_zip_tamper_is_detectable(self):
        a=io.BytesIO()
        with zipfile.ZipFile(a,"w") as z:z.writestr("projectready-nas/SKILL.md",b"original")
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w") as z:z.writestr("projectready-nas/SKILL.md",b"altered")
        self.assertNotEqual(hashlib.sha256(a.getvalue()).hexdigest(),hashlib.sha256(b.getvalue()).hexdigest())
    def test_synthetic_zip_slip_and_symlink_flags(self):
        a=io.BytesIO()
        with zipfile.ZipFile(a,"w") as z:
            z.writestr("../escape",b"bad")
            m=zipfile.ZipInfo("projectready-nas/link")
            m.create_system=3
            m.external_attr=(stat.S_IFLNK|0o777)<<16
            z.writestr(m,b"../../secret")
        with zipfile.ZipFile(io.BytesIO(a.getvalue())) as z:
            self.assertTrue(any(".." in name.split("/") for name in z.namelist()))
            self.assertTrue(any(((m.external_attr>>16)&0o170000)==stat.S_IFLNK for m in z.infolist()))
    def test_known_restricted_path_python_gap_is_not_hidden(self):
        # Confirms existing GAP, not a successful security control.
        x=check_presence((Requirement("restricted","delivery/.env"),),snap("delivery/.env"))
        self.assertEqual(x.checks[0].verdict,Verdict.PASS)
    def test_real_symlink_target_has_no_evidence_field(self):
        self.assertNotIn("resolved_target",FileEvidence.__dataclass_fields__)
if __name__=="__main__":unittest.main()
