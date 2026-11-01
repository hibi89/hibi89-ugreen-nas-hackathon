"""G158 local owner pairing security regression, synthetic inputs only in public CI."""
from __future__ import annotations
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flowpilot_g158_review_pair as pair


class G158ReviewPairTests(unittest.TestCase):
    def setUp(self):
        self.pdf = b'%PDF-1.4\nsynthetic\n%%EOF'
        self.members = {'flowpilot-3/SKILL.md': b'synthetic markdown skill',
                        'flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md': b'safe markdown',
                        'flowpilot-3/references/SAFETY_AND_SCENARIOS.md': b'safe markdown'}
        z = io.BytesIO()
        with ZipFile(z, 'w', ZIP_DEFLATED) as archive:
            for name, blob in self.members.items():
                archive.writestr(name, blob)
        self.skill = z.getvalue()
        self.patcher1 = patch.object(pair, 'PDF_PIN', pair._sha(self.pdf))
        self.patcher2 = patch.object(pair, 'SKILL_PIN', pair._sha(self.skill))
        self.patcher3 = patch.object(pair.owner, 'MEMBERS',
                                     {n: pair._sha(b) for n, b in self.members.items()})
        self.patcher4 = patch.object(pair.proposal, 'audit_pdf', return_value={
            'answer_count':10, 'substantive_answer_word_count':279, 'owner_internal_labels_present':False})
        for p in (self.patcher1, self.patcher2, self.patcher3, self.patcher4):
            p.start(); self.addCleanup(p.stop)

    def test_valid_synthetic_pair_roundtrip_hold(self):
        blob = pair.package_bytes(self.pdf, self.skill)
        result = pair.verify_package(blob)
        self.assertEqual(result['release_gate'], 'HOLD')
        self.assertEqual(result['pdf_answer_count'], 10)
        self.assertFalse(result['owner_approved'])
        self.assertFalse(result['official_checker_executed'])

    def test_package_exact_four_files_no_old_manifest(self):
        blob = pair.package_bytes(self.pdf, self.skill)
        with ZipFile(io.BytesIO(blob)) as z:
            self.assertEqual(set(z.namelist()), set(pair.PACKAGE_ENTRIES))
            self.assertNotIn(pair.owner.MANIFEST, z.namelist())
            self.assertNotIn('uliya-skill-kit-0.7.3-en.zip', z.namelist())

    def test_modified_pdf_refused(self):
        with self.assertRaisesRegex(pair.PairRefused, 'G157_PDF_PIN_MISMATCH'):
            pair.package_bytes(self.pdf + b'changed', self.skill)

    def test_modified_skill_refused(self):
        with self.assertRaisesRegex(pair.PairRefused, 'G147_SKILL_PIN_MISMATCH'):
            pair.package_bytes(self.pdf, self.skill + b'changed')

    def test_manifest_approval_stealth_change_refused(self):
        m = pair._manifest(self.pdf, self.skill)
        m['owner_approved'] = True
        with self.assertRaisesRegex(pair.PairRefused, 'G158_PAIR_MANIFEST_DRIFT'):
            pair.verify_pair(self.pdf, self.skill, json.dumps(m).encode())

    def test_manifest_forged_checker_result_refused(self):
        m = pair._manifest(self.pdf, self.skill)
        m['first_party_checker_executed'] = True
        with self.assertRaisesRegex(pair.PairRefused, 'G158_PAIR_MANIFEST_DRIFT'):
            pair.verify_pair(self.pdf, self.skill, json.dumps(m).encode())

    def test_duplicate_json_manifest_key_refused(self):
        m = pair._manifest(self.pdf, self.skill)
        raw=json.dumps(m).encode()
        with self.assertRaises(pair.PairRefused):
            pair.verify_pair(self.pdf, self.skill, b'{"schema":"wrong",' + raw[1:])

    def test_unrelated_archive_member_refused(self):
        original=pair.package_bytes(self.pdf,self.skill)
        content={}
        with ZipFile(io.BytesIO(original)) as z:
            content={n:z.read(n) for n in z.namelist()}
        content['evil.txt']=b'evil'
        altered=io.BytesIO()
        with ZipFile(altered,'w',ZIP_DEFLATED) as z:
            for name,blob in content.items():z.writestr(name,blob)
        with self.assertRaisesRegex(pair.PairRefused,'OWNER_BUNDLE_MEMBERS'):
            pair.verify_package(altered.getvalue())

    def test_readme_tampering_refused(self):
        original=pair.package_bytes(self.pdf,self.skill)
        with ZipFile(io.BytesIO(original)) as z:
            content={n:z.read(n) for n in z.namelist()}
        content[pair.README_NAME] = b'Submit instantly!'
        altered=io.BytesIO()
        with ZipFile(altered,'w',ZIP_DEFLATED) as z:
            for name,blob in content.items():z.writestr(name,blob)
        with self.assertRaisesRegex(pair.PairRefused,'OWNER_BUNDLE_INSTRUCTIONS_DRIFT'):
            pair.verify_package(altered.getvalue())

    def test_refuse_empty_answer_report(self):
        with patch.object(pair.proposal,'audit_pdf',return_value={
            'answer_count':9,'substantive_answer_word_count':275,'owner_internal_labels_present':False}):
            with self.assertRaisesRegex(pair.PairRefused,'G157_PDF_CONTENT_UNAPPROVED'):
                pair.package_bytes(self.pdf,self.skill)

    def test_no_overwrite_local_owner_archive(self):
        with TemporaryDirectory() as d:
            base=Path(d)
            pdf=base/'owner.pdf'; pdf.write_bytes(self.pdf)
            skill=base/'skill.zip'; skill.write_bytes(self.skill)
            out=base/'previous.zip'; out.write_bytes(b'unchanged')
            with self.assertRaisesRegex(pair.PairRefused,'DESTINATION_EXISTS_OR_UNSAFE'):
                pair.build(pdf,skill,out)
            self.assertEqual(out.read_bytes(),b'unchanged')

    def test_build_package_and_verify(self):
        with TemporaryDirectory() as d:
            base=Path(d)
            pdf=base/'owner.pdf'; pdf.write_bytes(self.pdf)
            skill=base/'skill.zip'; skill.write_bytes(self.skill)
            out=base/'review.zip'
            result=pair.build(pdf,skill,out)
            self.assertTrue(out.is_file())
            self.assertEqual(result['release_gate'],'HOLD')
            self.assertEqual(pair.verify_package(out.read_bytes())['release_gate'],'HOLD')

    def test_vendor_code_never_executed_by_local_bundle(self):
        source=Path(pair.__file__).read_text()
        for snippet in ('subprocess.run(', 'urllib.request', 'requests.post(', 'git clone'):
            self.assertNotIn(snippet, source)


if __name__ == '__main__':
    unittest.main()
