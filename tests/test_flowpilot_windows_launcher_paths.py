"""Static Windows launcher path contract (no PowerShell process / private Git)."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
NAMES = ("run_four_source_doctor.ps1",
         "run_four_source_synthetic.ps1",
         "run_four_source_suite.ps1")


class LocalWindowsLauncherPathTests(unittest.TestCase):
    def test_source_roots_resolve_relative_to_checkout_not_cwd(self):
        for name in NAMES:
            with self.subTest(name=name):
                content = (ROOT / "tools" / name).read_text(encoding="utf-8")
                self.assertIn("$repo = Split-Path -Parent $PSScriptRoot", content)
                self.assertIn("function Resolve-SourceRoot", content)
                self.assertIn("Join-Path $repo $Value", content)
                self.assertIn("[System.IO.Path]::IsPathRooted($Value)", content)
                for arg in ("$HaeRoot", "$SoviaRoot", "$DbvoraRoot"):
                    self.assertIn(f"{arg} = Resolve-SourceRoot {arg}", content)

    def test_default_sources_are_fixed_sibling_repository_names(self):
        for name in NAMES:
            with self.subTest(name=name):
                text = (ROOT / "tools" / name).read_text(encoding="utf-8")
                for directory in ("HAE", "SOVIA_sovereign", "DBVORA"):
                    self.assertIn("..\\" + directory, text)
                self.assertNotIn("Invoke-WebRequest", text)
                self.assertNotIn("git clone", text)

    def test_default_no_synthetic_writes_without_switch(self):
        for name in ("run_four_source_synthetic.ps1", "run_four_source_suite.ps1"):
            with self.subTest(name=name):
                content = (ROOT / "tools" / name).read_text(encoding="utf-8")
                self.assertIn("[switch]$ApproveDisposableSynthetic", content)
                self.assertIn("if ($ApproveDisposableSynthetic)", content)

    def test_suite_output_path_also_resolves_from_checkout(self):
        content = (ROOT / "tools" / "run_four_source_suite.ps1").read_text()
        self.assertIn("Join-Path $repo $OutputDir", content)
        self.assertIn("IsPathRooted($OutputDir)", content)
        self.assertIn('exit $LASTEXITCODE', content)


if __name__ == "__main__":
    unittest.main()
