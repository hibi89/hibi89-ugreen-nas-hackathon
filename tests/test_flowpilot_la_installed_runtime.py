"""Run a *real* installed private Lightning Azent acceptance when available.

Default UGREEN public CI has no access to the private HAE package: skip is an
honest missing-environment signal, never a successful integration claim.
Owners can set FLOWPILOT_REQUIRE_INSTALLED_LA=1 to fail when absent.
No NAS, network, customer data or credentials.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_la_synthetic_import import APPROVAL, run_demo


class IndependentNativeLAAcceptance(unittest.TestCase):
    def test_actual_installed_la_sqlite_receipts(self):
        required = os.getenv("FLOWPILOT_REQUIRE_INSTALLED_LA") == "1"
        try:
            found = importlib.util.find_spec("lightning_azent") is not None
        except (ImportError, ValueError):
            found = False
        if not found and not required:
            self.skipTest("private LA package not installed; native run NOT VERIFIED")
        self.assertTrue(found, "FLOWPILOT_REQUIRE_INSTALLED_LA=1 but private LA package unavailable")
        result = run_demo(approval=APPROVAL)
        self.assertEqual(result["status"], "SYNTHETIC_LA_SQLITE_VERIFIED",
                         "real LA acceptance failed: " + result["status"])
        self.assertTrue(result["la_executor_called"])
        self.assertTrue(result["la_execution_verified"])
        self.assertTrue(result["metadata_audit_observed"])
        self.assertTrue(result["replay_verified"])
        self.assertTrue(result["source_hash_preserved"])
        self.assertEqual(result["persisted_rows"], 2)
        self.assertFalse(result["uliya_or_nas_called"])
        self.assertFalse(result["hae_application_called"])


if __name__ == "__main__":
    unittest.main()
