"""G80 Creator candidate: consent, provenance, source parity and release HOLD tests."""
import copy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from flowpilot3_creator_pair import (PIN, NAME, MEMBER, PDF_NAME, ZIP_NAME,
                                    MANIFEST_NAME, build, validate_skill, validate_qa)

QA_PATH = ROOT / 'docs/submission/flowpilot3_creator_round1_qa_20261031.json'


class CreatorPairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qa = json.loads(QA_PATH.read_text(encoding='utf-8'))
        cls.synthetic_skill = (
            b'---\nname: flowpilot-3\ndescription: Safe owner-review Skill\n---\n'
            b'# Bounded evidence\nCHECK_REQUIRED REVIEW_VERSIONS HANDOFF_AUDIT '
            b'SUMMARIZE_SELECTED file-agent document-agent\n'
        )
        cls.synthetic_sha = sha256(cls.synthetic_skill).hexdigest()

    def fixture_qa(self):
        obj = copy.deepcopy(self.qa)
        obj['source_skill_sha256'] = self.synthetic_sha
        return obj

    def test_exact_official_questions_and_word_cap(self):
        self.assertEqual(PIN, self.qa['source_skill_sha256'])
        self.assertEqual(validate_qa(self.qa), 345)
        self.assertEqual(NAME, self.qa['candidate_name'])

    def test_synthetic_skill_requires_explicit_test_pin(self):
        validate_skill(self.synthetic_skill, expected_sha=self.synthetic_sha)
        with self.assertRaisesRegex(ValueError, 'source hash'):
            validate_skill(self.synthetic_skill)

    def test_source_identity_mismatch_refused(self):
        wrong = self.synthetic_skill.replace(b'flowpilot-3', b'flowpilot-nas')
        with self.assertRaisesRegex(ValueError, 'identity'):
            validate_skill(wrong, expected_sha=sha256(wrong).hexdigest())

    def test_missing_expert_or_intent_refused(self):
        wrong = self.synthetic_skill.replace(b'document-agent', b'not-registered')
        with self.assertRaisesRegex(ValueError, 'delegated'):
            validate_skill(wrong, expected_sha=sha256(wrong).hexdigest())

    def test_sensitive_source_refused(self):
        wrong = self.synthetic_skill + b'\nghp_' + b'A'*25
        with self.assertRaisesRegex(ValueError, 'credential'):
            validate_skill(wrong, expected_sha=sha256(wrong).hexdigest())

    def test_wrong_edition_and_legacy_sha_refused(self):
        for field, value in [
            ('project', 'ProjectReady'),
            ('candidate_name', 'flowpilot-nas'),
            ('source_skill_sha256', '47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b'),
            ('status', 'SUBMITTED'),
            ('official_creator_evidence', 'VERIFIED'),
        ]:
            with self.subTest(field=field):
                obj = copy.deepcopy(self.qa)
                obj[field] = value
                with self.assertRaises(ValueError):
                    validate_qa(obj)

    def test_forged_clean_checker_refused(self):
        obj = copy.deepcopy(self.qa)
        obj['checker_evidence']['warnings'] = []
        obj['checker_evidence']['status'] = 'static-pass'
        with self.assertRaisesRegex(ValueError, 'Checker warning'):
            validate_qa(obj)

    def test_wrong_official_question_refused(self):
        obj = copy.deepcopy(self.qa)
        obj['questions'][0]['question'] = 'Changed'
        with self.assertRaisesRegex(ValueError, 'questions differ'):
            validate_qa(obj)

    def test_missing_disclosure_refused(self):
        obj = copy.deepcopy(self.qa)
        obj['disclosure'] = 'Unspecified'
        with self.assertRaisesRegex(ValueError, 'disclosure missing'):
            validate_qa(obj)

    def test_excess_words_refused(self):
        obj = copy.deepcopy(self.qa)
        obj['questions'][1]['answer'] = 'overflow '*501
        with self.assertRaisesRegex(ValueError, '500'):
            validate_qa(obj)

    @unittest.skipUnless(importlib.util.find_spec('reportlab') and importlib.util.find_spec('pypdf'),
                         'PDF build dependencies unavailable')
    def test_creates_exact_review_pdf_zip_and_preserves_hold(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / 'input'
            input_dir.mkdir()
            skill = input_dir / 'SKILL.md'
            skill.write_bytes(self.synthetic_skill)
            qa = input_dir / 'qa.json'
            qa.write_text(json.dumps(self.fixture_qa()), encoding='utf-8')
            out = root / 'output'
            report = build(skill, qa, out, expected_sha=self.synthetic_sha)
            self.assertEqual(report['release_gate'], 'HOLD')
            self.assertFalse(report['owner_approved_release'])
            self.assertFalse(report['devpost_submitted'])
            self.assertEqual(report['checker_report']['warnings'],
                             ['DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE'])
            self.assertEqual(report['creator_evidence'], 'OWNER_REPORTED_NOT_INDEPENDENTLY_VERIFIED')
            self.assertEqual(report['substantive_words'], 345)
            self.assertEqual(report['pdf_pages'], 1)
            self.assertEqual(report['zip_members'], [MEMBER])
            self.assertEqual(report['pdf_sha256'], sha256((out / PDF_NAME).read_bytes()).hexdigest())
            self.assertEqual(report['zip_sha256'], sha256((out / ZIP_NAME).read_bytes()).hexdigest())
            self.assertEqual(json.loads((out / MANIFEST_NAME).read_text()), report)
            with ZipFile(out / ZIP_NAME) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.namelist(), [MEMBER])
                self.assertEqual(z.read(MEMBER), self.synthetic_skill)
            before = {p.name: sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
            with self.assertRaisesRegex(ValueError, 'Existing reviewer artifact'):
                build(skill, qa, out, expected_sha=self.synthetic_sha)
            after = {p.name: sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
            self.assertEqual(before, after)

    def test_preexisting_manifest_aborts_before_any_write(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / 'SKILL.md'
            skill.write_bytes(self.synthetic_skill)
            qa = root / 'qa.json'
            qa.write_text(json.dumps(self.fixture_qa()), encoding='utf-8')
            out = root / 'existing'
            out.mkdir()
            (out / MANIFEST_NAME).write_text('KEEP', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Existing reviewer artifact'):
                build(skill, qa, out, expected_sha=self.synthetic_sha)
            self.assertEqual([p.name for p in out.iterdir()], [MANIFEST_NAME])


if __name__ == '__main__':
    unittest.main()
