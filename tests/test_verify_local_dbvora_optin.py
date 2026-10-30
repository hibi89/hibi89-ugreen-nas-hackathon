"""Private DBVORA reader may never load before exact owner approval."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from tools.verify_local_metadata_la_chain import (
    EXPECTED_DBVORA_SHA, load_pinned_dbvora_reader, verify,
)
from tools.verify_private_hae_chain import ProofRefused


class PrivateDBVORAOptInTests(unittest.TestCase):
    def test_no_readonly_metadata_approval_fails_before_any_checkout(self):
        with patch("tools.verify_local_metadata_la_chain.verify_checkout",
                   side_effect=AssertionError("checkout not allowed")):
            with self.assertRaisesRegex(ProofRefused, "DBVORA_REQUIRES_EXACT_PLAN_APPROVAL"):
                verify(Path("/HAE"), Path("/SOVIA"), "파일 누락 확인",
                       Path("/synthetic"), ["README.md"], dbvora_root=Path("/DBVORA"))

    def test_no_plan_hash_fails_before_any_checkout(self):
        with patch("tools.verify_local_metadata_la_chain.verify_checkout",
                   side_effect=AssertionError("checkout not allowed")):
            with self.assertRaisesRegex(ProofRefused, "DBVORA_REQUIRES_EXACT_PLAN_APPROVAL"):
                verify(Path("/HAE"), Path("/SOVIA"), "파일 누락 확인",
                       Path("/synthetic"), ["README.md"],
                       metadata_consent=True, dbvora_root=Path("/DBVORA"))

    def test_private_checkout_mismatch_is_rejected(self):
        self.assertEqual(len(EXPECTED_DBVORA_SHA), 40)
        with patch("tools.verify_local_metadata_la_chain.verify_checkout",
                   side_effect=ProofRefused("SOURCE_SHA_MISMATCH")):
            with self.assertRaisesRegex(ProofRefused, "SOURCE_SHA_MISMATCH"):
                load_pinned_dbvora_reader(Path("/untrusted"))


if __name__ == "__main__":
    unittest.main()
