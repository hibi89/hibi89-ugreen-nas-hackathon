"""Reject mismatched Python import modules despite an apparent pinned checkout.

Synthetic code and checkout files only; never import private repositories in CI.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.verify_private_hae_chain import (
    ProofRefused, require_pinned_import_origins,
)


class PinnedImportOriginTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="ugreen-import-provenance-")
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.hae = self.base / "HAE"
        self.sovia = self.base / "SOVIA"
        self.runtime = (self.hae / "packages" / "lightning-azent" /
                        "lightning_azent" / "runtime.py")
        self.assessor = self.sovia / "sovia_la_plan_preflight.py"
        self.runtime.parent.mkdir(parents=True)
        self.assessor.parent.mkdir(parents=True)
        self.runtime.write_text("# fake LA source path only\n", encoding="utf-8")
        self.assessor.write_text("# fake SOVIA source path only\n", encoding="utf-8")

    @staticmethod
    def _function(path):
        namespace = {}
        exec(compile("def preflight(plan):\n    return None\n",
                     str(path), "exec"), namespace)
        return namespace["preflight"]

    def test_matching_import_origin_paths_accepted_for_synthetic_functions(self):
        class Engine:
            preflight = None
        Engine.preflight = staticmethod(self._function(self.runtime))
        assess = self._function(self.assessor)
        require_pinned_import_origins(self.hae, self.sovia, Engine, assess)

    def test_cached_wrong_hae_runtime_is_rejected(self):
        class Engine:
            preflight = None
        wrong_runtime = self.base / "another" / "runtime.py"
        wrong_runtime.parent.mkdir()
        wrong_runtime.write_text("# unrelated synthetic source\n")
        Engine.preflight = staticmethod(self._function(wrong_runtime))
        with self.assertRaisesRegex(ProofRefused, "PINNED_LA_RUNTIME_IMPORT_MISMATCH"):
            require_pinned_import_origins(
                self.hae, self.sovia, Engine, self._function(self.assessor)
            )

    def test_cached_wrong_sovia_assessor_is_rejected(self):
        class Engine:
            preflight = None
        Engine.preflight = staticmethod(self._function(self.runtime))
        wrong = self.base / "another" / "sovia_la_plan_preflight.py"
        wrong.parent.mkdir()
        wrong.write_text("# unrelated synthetic source\n")
        with self.assertRaisesRegex(ProofRefused, "PINNED_SOVIA_IMPORT_MISMATCH"):
            require_pinned_import_origins(
                self.hae, self.sovia, Engine, self._function(wrong)
            )

    def test_missing_verified_source_file_rejected(self):
        class Engine:
            preflight = None
        Engine.preflight = staticmethod(self._function(self.runtime))
        self.runtime.unlink()
        with self.assertRaisesRegex(ProofRefused, "PINNED_LA_RUNTIME_IMPORT_MISMATCH"):
            require_pinned_import_origins(
                self.hae, self.sovia, Engine, self._function(self.assessor)
            )

    def test_unverifiable_callable_is_rejected(self):
        class Engine:
            preflight = object()
        with self.assertRaisesRegex(ProofRefused, "PINNED_LA_RUNTIME_IMPORT_MISMATCH"):
            require_pinned_import_origins(
                self.hae, self.sovia, Engine, self._function(self.assessor)
            )


if __name__ == "__main__":
    unittest.main()
