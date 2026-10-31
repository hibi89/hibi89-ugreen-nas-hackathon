"""Synthetic-only G154 owner offline packaging/validation regressions.

No real G147/third-party vendor bytes are required in public CI.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flowpilot_g154_owner_offline_bundle as g154


class TestG154OfflineOwnerBundle(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.folder = self.base / 'candidate'
        self.folder.mkdir()
        self.pdf = b'%PDF-1.4\nsynthetic pdf\n%%EOF'
        self.md = {
            'flowpilot-3/SKILL.md':
                (b'---\nname: flowpilot-3\ndescription: test\n---\n'
                 b'[Cap](references/CAPABILITY_AND_PLAN_CONTRACT.md)\n'
                 b'[Safe](references/SAFETY_AND_SCENARIOS.md)\n'
                 b'hackathon-original chatgpt third-party registered rights check\n'),
            'flowpilot-3/references/CAPABILITY_AND_PLAN_CONTRACT.md': b'# Cap\nsynthetic\n',
            'flowpilot-3/references/SAFETY_AND_SCENARIOS.md': b'# Safe\nsynthetic\n',
        }
        stream = BytesIO()
        with ZipFile(stream, 'w', ZIP_DEFLATED) as z:
            for name, blob in self.md.items():
                z.writestr(name, blob)
        self.zip = stream.getvalue()
        self.local_pins = {g154.PDF: sha256(self.pdf).hexdigest(),
                           g154.ZIP: sha256(self.zip).hexdigest()}
        self.local_members = {key: sha256(value).hexdigest() for key, value in self.md.items()}
        self.manifest = {
            'schema': 'g147-exact-owner-review-v1',
            'release_gate': 'HOLD', 'owner_review_only': True,
            'first_party_checker_executed': False,
            'registered_uliya_expert_verified': False,
            'real_nas_verified': False, 'devpost_submitted': False,
            'substantive_english_word_count': 50, 'pdf_pages': 1,
            'package_member_count': 3,
            'package_members': [{'name': n, 'bytes': len(b), 'sha256': sha256(b).hexdigest()}
                                for n, b in self.md.items()],
            'artifacts': {
                g154.PDF: {'bytes': len(self.pdf), 'sha256': sha256(self.pdf).hexdigest()},
                g154.ZIP: {'bytes': len(self.zip), 'sha256': sha256(self.zip).hexdigest()}
            }
        }
        self._save()
        self.patch_pins = patch.dict(g154.PINS, self.local_pins, clear=True)
        self.patch_members = patch.dict(g154.MEMBERS, self.local_members, clear=True)
        self.patch_pins.start(); self.patch_members.start()
        self.addCleanup(self.patch_pins.stop)
        self.addCleanup(self.patch_members.stop)

    def _save(self):
        (self.folder / g154.PDF).write_bytes(self.pdf)
        (self.folder / g154.ZIP).write_bytes(self.zip)
        (self.folder / g154.MANIFEST).write_text(json.dumps(self.manifest), encoding='utf-8')

    def test_valid_synthetic_pair_is_not_official_pass(self):
        result = g154.verify_folder(self.folder)
        self.assertEqual(result['status'], 'EXACT_G147_OFFLINE_PAIR_PASS_NOT_OFFICIAL')
        self.assertFalse(result['official_checker_executed'])
        self.assertEqual(result['release_gate'], 'HOLD')

    def test_wrong_pdf_digest_fails_closed(self):
        (self.folder / g154.PDF).write_bytes(self.pdf + b'changed')
        with self.assertRaises(g154.Refused): g154.verify_folder(self.folder)

    def test_missing_member_fails_closed(self):
        z = BytesIO()
        with ZipFile(z, 'w') as a: a.writestr('flowpilot-3/SKILL.md', self.md['flowpilot-3/SKILL.md'])
        shortened = z.getvalue()
        self.manifest['artifacts'][g154.ZIP] = {'bytes': len(shortened), 'sha256': sha256(shortened).hexdigest()}
        with patch.dict(g154.PINS, {g154.ZIP: sha256(shortened).hexdigest()}):
            with self.assertRaisesRegex(g154.Refused, 'INVALID_MARKDOWN_MEMBERS'):
                g154.verify_bytes(self.pdf, shortened, json.dumps(self.manifest).encode())

    def test_manifest_claimed_official_checker_refused(self):
        self.manifest['first_party_checker_executed'] = True
        self._save()
        with self.assertRaisesRegex(g154.Refused, 'RELEASE_METADATA'):
            g154.verify_folder(self.folder)

    def test_duplicate_manifest_key_refused(self):
        original = (self.folder / g154.MANIFEST).read_bytes()
        repeated = b'{"schema": "duplicate",' + original[1:]
        with self.assertRaises(g154.Refused):
            g154.verify_bytes(self.pdf, self.zip, repeated)

    def test_build_real_zip_and_verify_archive_roundtrip(self):
        output = self.base / 'owner-offline.zip'
        result = g154.build(self.folder, output)
        self.assertEqual(result['status'], 'G154_PRIVATE_OFFLINE_PACKAGE_BUILT_NOT_SUBMITTED')
        self.assertTrue(output.is_file())
        self.assertEqual(g154.verify_package(output.read_bytes())['release_gate'], 'HOLD')
        with ZipFile(output) as z:
            self.assertEqual(set(z.namelist()), set(g154.PACKAGE_FILES) | {g154.BUNDLE_MANIFEST})
            self.assertNotIn('uliya-skill-kit-0.7.3-en.zip', z.namelist())

    def test_no_overwrite_existing_owner_bundle(self):
        output = self.base / 'existing.zip'
        output.write_bytes(b'unchanged')
        with self.assertRaisesRegex(g154.Refused, 'OUTPUT_EXISTS'):
            g154.build(self.folder, output)
        self.assertEqual(output.read_bytes(), b'unchanged')

    def test_tampered_package_refused(self):
        output = self.base / 'owner-bundle.zip'
        g154.build(self.folder, output)
        raw = output.read_bytes()
        with self.assertRaises(g154.Refused):
            g154.verify_package(raw[:-16])

    def test_symlink_owner_input_refused(self):
        target = self.base / 'outside.pdf'
        target.write_bytes(self.pdf)
        item = self.folder / g154.PDF
        item.unlink()
        try:
            item.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks not permitted')
        with self.assertRaises(g154.Refused): g154.verify_folder(self.folder)

    def test_cli_bad_input_refuses_without_private_path(self):
        with redirect_stdout(StringIO()) as out:
            rc = g154.main(['--verify-folder', str(self.base / 'secret-folder')])
        self.assertEqual(rc, 2)
        self.assertNotIn(str(self.base), out.getvalue())
        self.assertIn('HOLD', out.getvalue())

    def test_no_network_or_vendor_calls_in_source(self):
        source = Path(g154.__file__).read_text(encoding='utf-8')
        for forbidden in ('urllib.request', 'requests.', 'subprocess.run(', 'git clone',
                          'node /vendor', 'docker run', 'http://', 'https://'):
            self.assertNotIn(forbidden, source)

    def test_package_refuses_bare_arbitrary_input(self):
        with self.assertRaises(g154.Refused): g154.verify_package(b'notzip')


if __name__ == '__main__':
    unittest.main()
