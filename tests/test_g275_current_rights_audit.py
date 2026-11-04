"""G275 read-only original candidate audit regression; no private files committed."""
import io
from pathlib import Path
from unittest.mock import patch
import sys
import unittest
from zipfile import ZipFile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools") if Path(__file__).resolve().parent.name == "tests" else str(Path(__file__).resolve().parent))
import g275_current_rights_audit as mod
from g275_current_rights_audit import (audit, AuditRefused, NAMES, MAIN, RIGHTS, KIT_SHA,
    SCHEMA, CANDIDATE_SHA, digest, zip_markdown)

FAKE_SKILL = b'---\nname: flowpilot-3\ndescription: test\n---\nmax-depth at most 5 and limit at most 200'
FAKE_RIGHTS = (b'Principal new work for the contest: x\nOpenAI AI assistance is disclosed\n'
    b"The Uliya Kit is UGREEN's official developer resource subject to its own terms.\n"
    b'Participant rights, final PDF/ZIP selection, external uploads, public publication\n'
    b'No vendor script, binary, SDK source')
def fixture(**replace):
    b=io.BytesIO()
    with ZipFile(b,'w') as z:
        for n in sorted(NAMES):
            if n in replace:
                content = replace[n]
            elif n == MAIN: content=FAKE_SKILL
            elif n == RIGHTS: content=FAKE_RIGHTS
            elif n.endswith('owner-evidence-contract.md'): content=b'including a chosen limit below 200'
            else: content=b'# unique new source: '+n.encode()
            z.writestr(n,content)
    return b.getvalue()

class G275Tests(unittest.TestCase):
    def test_shape_accepts_five_nonempty_markdown(self):
        x=zip_markdown(fixture(),expected=NAMES,max_files=5)
        self.assertEqual(set(x),set(NAMES))
    def test_reject_missing_member(self):
        b=io.BytesIO()
        with ZipFile(b,'w') as z:
            for n in sorted(NAMES)[:-1]:z.writestr(n,'good')
        with self.assertRaises(AuditRefused):zip_markdown(b.getvalue(),expected=NAMES,max_files=5)
    def test_reject_duplicate_member(self):
        b=io.BytesIO()
        with ZipFile(b,'w') as z:
            for n in sorted(NAMES):z.writestr(n,'good')
            z.writestr(MAIN,'duplicate')
        with self.assertRaises(AuditRefused):zip_markdown(b.getvalue(),expected=NAMES,max_files=6)
    def test_reject_traversal_member(self):
        b=io.BytesIO()
        with ZipFile(b,'w') as z:
            for n in sorted(NAMES):z.writestr('../bad.md' if n==MAIN else n,'good')
        with self.assertRaises(AuditRefused):zip_markdown(b.getvalue(),expected=NAMES,max_files=5)
    def test_reject_binary(self):
        with self.assertRaises(AuditRefused):zip_markdown(fixture(**{MAIN:b'\x00'}),expected=NAMES,max_files=5)
    def test_fail_unpinned_source(self):
        with self.assertRaisesRegex(AuditRefused,'CANDIDATE_SHA_MISMATCH'):
            audit(fixture(),b'fake kit')
    def test_fail_forged_kit_digest(self):
        with self.assertRaisesRegex(AuditRefused,'VENDOR_KIT_SHA_MISMATCH'):
            audit(fixture(),b'fake kit',candidate_sha=digest(fixture()))
    def test_fail_disclosure_if_bad(self):
        archive=fixture(**{RIGHTS:b'no license info'})
        # Prioritize right missing only with a pinned official kit digest, verified in exact file test.
        self.assertNotIn(b'OpenAI AI assistance',zip_markdown(archive,expected=NAMES,max_files=5)[RIGHTS])
    def fake_kit(self, *, vendor=b'# An unrelated vendor document'):
        b=io.BytesIO()
        with ZipFile(b,'w') as z:z.writestr('uliya-skill-kit/SKILL.md',vendor)
        return b.getvalue()
    def test_synthetic_complete_boundary_pass_is_not_legal_approval(self):
        candidate,kit=fixture(),self.fake_kit()
        with patch.object(mod,'KIT_SHA',digest(kit)):
            result=audit(candidate,kit,candidate_sha=digest(candidate))
        self.assertEqual(result['release_gate'],'HOLD')
        self.assertEqual(result['owner_license_or_rights_attestation'],'NOT_APPROVED')
        self.assertEqual(result['earned_new_completion_pct_points'],0)
        self.assertFalse(result['vendor_whole_markdown_reused'])
    def test_reject_whole_vendor_markdown_reuse(self):
        candidate=fixture()
        kit=self.fake_kit(vendor=FAKE_SKILL)
        with patch.object(mod,'KIT_SHA',digest(kit)):
            with self.assertRaisesRegex(AuditRefused,'VENDOR_MARKDOWN_WHOLE_FILE_REUSE'):
                audit(candidate,kit,candidate_sha=digest(candidate))
    def test_reject_missing_rights_disclosure(self):
        candidate=fixture(**{RIGHTS:b'no disclosures'})
        kit=self.fake_kit()
        with patch.object(mod,'KIT_SHA',digest(kit)):
            with self.assertRaisesRegex(AuditRefused,'SOURCE_DISCLOSURE'):
                audit(candidate,kit,candidate_sha=digest(candidate))
    def test_reject_embedded_secret(self):
        candidate=fixture(**{RIGHTS:FAKE_RIGHTS+b'\nghp_' + b'Z'*24})
        kit=self.fake_kit()
        with patch.object(mod,'KIT_SHA',digest(kit)):
            with self.assertRaisesRegex(AuditRefused,'SECRET'):
                audit(candidate,kit,candidate_sha=digest(candidate))
    def test_reject_outdated_discovery_guard(self):
        candidate=fixture(**{MAIN:FAKE_SKILL.replace(b'max-depth at most 5 and limit at most 200',b'unbounded listing')})
        kit=self.fake_kit()
        with patch.object(mod,'KIT_SHA',digest(kit)):
            with self.assertRaisesRegex(AuditRefused,'MISSING_G274_GUARD'):
                audit(candidate,kit,candidate_sha=digest(candidate))
    def test_explicit_no_release(self):
        self.assertIn('LICENSE_NOT_CLEARED', 'CURRENT_G274_SOURCE_BOUNDARY_PASS_LICENSE_NOT_CLEARED')
        self.assertTrue(SCHEMA.endswith('-v1'))
        self.assertEqual(len(CANDIDATE_SHA),64)
        self.assertEqual(len(KIT_SHA),64)

if __name__ == '__main__':unittest.main()
