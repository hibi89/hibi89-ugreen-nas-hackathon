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
    def archive(self, path, *, unbounded=False, low_limit=False, extra=False):
        main = '\n'.join(mod.CHECKS[mod.MAIN])
        ref = '\n'.join(mod.CHECKS[mod.CONTRACT])
        if unbounded:
            main = main.replace('Never use unbounded ls', 'ls, find or stat in that folder')
        if low_limit:
            ref = ref.replace('including a chosen limit below 200', 'if 200 entries are reached')
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr(mod.MAIN, main)
            z.writestr(mod.CONTRACT, ref)
            for i in range(3):
                z.writestr(mod.ROOT + f'references/safe-{i}.md', '# Safe')
            if extra:
                z.writestr(mod.ROOT + 'unsafe.py', 'bad')

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


if __name__ == '__main__':
    unittest.main()
