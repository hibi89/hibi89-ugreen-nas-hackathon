"""G156 published rule audit tests: synthetic only, no owner data in CI."""
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flowpilot_g156_public_rules_gate as rules


class PublishedRuleAuditTests(unittest.TestCase):
    def setUp(self):
        self.skill = ("---\nname: flowpilot-3\ndescription: Scope-bound NAS planning\n---\n"
                      "hackathon-original third-party license chatgpt rights check "
                      "registered and has not run on real NAS\n")
        self.refs = {'flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md': 'hello',
                     'flowpilot-3/references/SAFETY_AND_SCENARIOS.md': 'hello'}
        self.patcher = patch.object(rules.owner, 'verify_bytes', return_value={
            'pdf_text_verified': False, 'skill_zip_sha256': 'synthetic-only'})
        self.check = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def audit(self, *, skill=None, refs=None):
        files = {'flowpilot-3/SKILL.md': (self.skill if skill is None else skill)}
        files.update(self.refs if refs is None else refs)
        b = io.BytesIO()
        with ZipFile(b, 'w', ZIP_DEFLATED) as z:
            for n, content in files.items():
                z.writestr(n, content)
        return rules.audit_bytes(b'%PDF-1.4\n%%EOF', b.getvalue(), b'{}')

    def test_valid_synthetic_rules_never_call_it_official(self):
        result = self.audit()
        self.assertEqual(result['release_gate'], 'HOLD')
        self.assertFalse(result['official_checker_executed'])
        self.assertTrue(result['frontmatter_slug_valid'])
        self.check.assert_called_once()

    def test_slug_uppercase_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_SKILL_NAME_INVALID'):
            self.audit(skill=self.skill.replace('flowpilot-3', 'FlowPilot'))

    def test_slug_over_64_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_SKILL_NAME_INVALID'):
            self.audit(skill=self.skill.replace('flowpilot-3', 'a' * 65))

    def test_description_over_1024_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_DESCRIPTION_INVALID'):
            self.audit(skill=self.skill.replace('Scope-bound NAS planning', 'a' * 1025))

    def test_duplicate_yaml_key_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_FRONTMATTER_KEYS'):
            self.audit(skill=self.skill.replace('description:', 'name: duplicate\ndescription:'))

    def test_binary_archive_member_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_ZIP_LIMITS'):
            self.audit(refs={**self.refs, 'flowpilot-3/run.sh': 'echo hello'})

    def test_missing_ai_disclosure_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_DISCLOSURE_INCOMPLETE'):
            self.audit(skill=self.skill.replace('chatgpt', 'undisclosed'))

    def test_todo_line_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_UNRESOLVED_MARKER'):
            self.audit(skill=self.skill+'\nTODO: fill in later\n')

    def test_mock_aws_key_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_SECRET_PATTERN'):
            self.audit(skill=self.skill+'\nAKIA' + 'Z' * 16 + '\n')

    def test_no_live_test_disclosure_refused(self):
        with self.assertRaisesRegex(rules.PublicRuleRefused, 'PUBLIC_UNTESTED_DISCLOSURE_MISSING'):
            self.audit(skill=self.skill.replace('has not run', 'performs'))

    def test_bad_owner_path_cli_refuses_without_leak(self):
        with TemporaryDirectory() as tmp:
            bad = Path(tmp) / 'secret-absent'
            stdout=io.StringIO()
            with redirect_stdout(stdout):
                rc=rules.main(['--folder', str(bad)])
            self.assertEqual(rc, 2)
            self.assertNotIn(str(bad), stdout.getvalue())
            self.assertEqual(json.loads(stdout.getvalue())['release_gate'], 'HOLD')


if __name__ == '__main__':
    unittest.main()
