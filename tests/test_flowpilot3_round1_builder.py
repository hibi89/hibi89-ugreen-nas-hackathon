"""Focused offline tests for Round 1 owner-review builder; no NAS or Devpost."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from flowpilot3_round1_builder import PIN, PROMPTS, build, sha, validate, verify_pdf


class Round1BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / 'skill/flowpilot-nas/SKILL.md').read_bytes()
        cls.qa = json.loads((ROOT / 'docs/submission/flowpilot3_round1_qa_20261029.json').read_text(encoding='utf-8'))

    def test_exact_source_and_500_word_cap(self):
        self.assertEqual(sha(self.skill), PIN)
        self.assertEqual([x['question'] for x in self.qa['questions']], PROMPTS)
        self.assertEqual(validate(self.skill, self.qa), 360)

    def test_pdf_zip_evidence_and_scope(self):
        with TemporaryDirectory() as d:
            result = build(ROOT / 'skill/flowpilot-nas/SKILL.md',
                           ROOT / 'docs/submission/flowpilot3_round1_qa_20261029.json', Path(d))
            self.assertEqual(result['pdf_pages'], 1)
            self.assertEqual(result['substantive_english_words'], 360)
            self.assertTrue(result['source_exact_match'])
            self.assertEqual(result['skill_members'], ['flowpilot-nas/SKILL.md'])
            self.assertFalse(result['legal_rights_released'])
            self.assertFalse(result['devpost_submitted'])
            self.assertEqual(result['official_creator'], 'NOT_RUN')
            self.assertTrue(result['local_prototype_excluded_from_zip'])
            self.assertEqual(verify_pdf(Path(d) / 'NAS_FlowPilot_3_Round1_OWNER_REVIEW.pdf', self.qa), 1)

    def test_modified_skill_refused(self):
        with self.assertRaises(ValueError):
            validate(self.skill+b'\n# Modified', self.qa)

    def test_status_cannot_claim_submission(self):
        bad=copy.deepcopy(self.qa)
        bad['status']='SUBMITTED'
        with self.assertRaises(ValueError):validate(self.skill,bad)

    def test_missing_disclosure_refused(self):
        bad=copy.deepcopy(self.qa)
        bad['disclosure']=''
        with self.assertRaises(ValueError):validate(self.skill,bad)

    def test_words_over_cap_refused(self):
        bad=copy.deepcopy(self.qa)
        bad['questions'][0]['answer']='overflow '*501
        with self.assertRaises(ValueError):validate(self.skill,bad)

    def test_official_prompts_cannot_change(self):
        bad=copy.deepcopy(self.qa)
        bad['questions'][8]['question']='unofficial prompt'
        with self.assertRaises(ValueError):validate(self.skill,bad)


if __name__=='__main__':unittest.main()
