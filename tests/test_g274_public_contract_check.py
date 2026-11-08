"""Synthetic, zero-network checks: no private ZIP is required in public CI."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

TOOL = Path(__file__).resolve().parent.parent / 'tools' / 'g274_public_contract_check.py'
if not TOOL.exists():
    TOOL = Path(__file__).with_name('g274_public_contract_check.py')
spec = importlib.util.spec_from_file_location('g274_contract', TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class G274ContractTests(unittest.TestCase):
    def archive(self, path, *, unbounded=False, low_limit=False, extra=False,
                corrupt_other=False, non_utf8_other=False, symlink_other=False,
                unlinked=False, unknown_member=False):
        main = '\n'.join(mod.CHECKS[mod.MAIN])
        ref = '\n'.join(mod.CHECKS[mod.CONTRACT])
        if unbounded:
            main = main.replace('Never use unbounded ls', 'ls, find or stat in that folder')
        if low_limit:
            ref = ref.replace('including a chosen limit below 200', 'if 200 entries are reached')
        for name in sorted(mod.EXPECTED_MEMBERS - {mod.MAIN, mod.CONTRACT}):
            if unlinked and name.endswith('failure-and-disclosure.md'):
                continue
            main += '\n' + name.removeprefix(mod.ROOT)
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
            z.writestr(mod.MAIN, main)
            z.writestr(mod.CONTRACT, ref)
            extras = sorted(mod.EXPECTED_MEMBERS - {mod.MAIN, mod.CONTRACT})
            for index, name in enumerate(extras):
                if unknown_member and index == 0:
                    name = mod.ROOT + 'references/unknown.md'
                data = b'REF-UNRELATED-CHECK-CRC' if index == 0 else b'# Safe reference'
                if non_utf8_other and index == 0:
                    data = b'\xff'
                if symlink_other and index == 0:
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = 0o120777 << 16
                    z.writestr(info, data)
                else:
                    z.writestr(name, data)
            if extra:
                z.writestr(mod.ROOT + 'unsafe.py', 'bad')
        if corrupt_other:
            blob = bytearray(path.read_bytes())
            index = blob.index(b'REF-UNRELATED-CHECK-CRC')
            blob[index] ^= 1
            path.write_bytes(blob)

    def test_accepts_bounded_synthetic_contract(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'good.zip'
            self.archive(p)
            result = mod.inspect(p)
            self.assertEqual(result['local_contract_check'], 'PASS')
            self.assertEqual(result['registered_nas'], 'NOT_RUN')
            self.assertEqual(result['release'], 'HOLD')

    def test_rejects_unbounded_initial_listing(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'bad.zip'
            self.archive(p, unbounded=True)
            with self.assertRaisesRegex(ValueError, 'bounded|unbounded'):
                mod.inspect(p)

    def test_rejects_fixed_200_truncation_bug(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'bad.zip'
            self.archive(p, low_limit=True)
            with self.assertRaisesRegex(ValueError, 'bounded|unbounded'):
                mod.inspect(p)

    def test_rejects_non_markdown_payload(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'bad.zip'
            self.archive(p, extra=True)
            with self.assertRaisesRegex(ValueError, 'count|member'):
                mod.inspect(p)

    def test_rejects_corrupt_unread_reference(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'corrupt.zip'
            self.archive(p, corrupt_other=True)
            with self.assertRaisesRegex(ValueError, 'CRC|unreadable'):
                mod.inspect(p)

    def test_rejects_non_utf8_unread_reference(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'nonutf8.zip'
            self.archive(p, non_utf8_other=True)
            with self.assertRaisesRegex(ValueError, 'unreadable'):
                mod.inspect(p)

    def test_rejects_symlink_reference(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'symlink.zip'
            self.archive(p, symlink_other=True)
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                mod.inspect(p)

    def test_rejects_unlinked_reference(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'unlinked.zip'
            self.archive(p, unlinked=True)
            with self.assertRaisesRegex(ValueError, 'unlinked'):
                mod.inspect(p)

    def test_rejects_unknown_member_at_same_count(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'unknown.zip'
            self.archive(p, unknown_member=True)
            with self.assertRaisesRegex(ValueError, 'member'):
                mod.inspect(p)


if __name__ == '__main__':
    unittest.main()
