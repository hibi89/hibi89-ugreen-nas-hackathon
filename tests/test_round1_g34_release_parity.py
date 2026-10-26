"""G34 exact-G32 source, official checker proof and isolated PDF/ZIP preview."""
import copy, hashlib, io, json, sys, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import round1_g34_release_parity as g34

class G34Tests(unittest.TestCase):
    def test_exact_static_checker_source(self):
        b = g34.pinned_source()
        self.assertEqual(g34.digest(b), g34.G32_SHA)
        self.assertEqual(len(b), 14389)
    def test_proposal_reconciles_stale_checker_claim(self):
        p = g34.staged_proposal()
        self.assertEqual(len(p["questions"]), 10)
        self.assertLessEqual(p["substantive_words"], 500)
        self.assertIn("first-party Uliya static checker", p["questions"][7]["answer"])
        self.assertNotIn("No official Uliya validator", p["questions"][7]["answer"])
        self.assertEqual(p["proof_status"]["official_validator"],
                         "G32_EXACT_SHA_FIRST_PARTY_STATIC_PASS")
        self.assertEqual(p["proof_status"]["devpost"], "NOT_SUBMITTED")
    def test_zip_byte_parity_and_determinism(self):
        from round1_official_creator_preview import zip_only_skill
        raw = g34.pinned_source()
        z = zip_only_skill(raw)
        self.assertEqual(z, zip_only_skill(raw))
        with zipfile.ZipFile(io.BytesIO(z)) as file:
            self.assertEqual(file.namelist(), ["projectready-nas/SKILL.md"])
            self.assertEqual(file.read(file.namelist()[0]), raw)
    def test_reject_source_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp)/"SKILL.md"
            bad.write_bytes(g34.pinned_source()+b"x")
            with patch.object(g34, "G32", bad):
                with self.assertRaisesRegex(ValueError, "SHA/size changed"):
                    g34.pinned_source()
    def test_reject_tampered_checker(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad_key, bad_value in (
                ("checker_result_status", "not-uploadable"),
                ("checker_exit_code", 1),
                ("skill_sha256_before_after", "0"*64),
                ("checker_summary", {"errors": 0, "warnings": 1, "info": 0}),
            ):
                j=json.loads(g34.G33.read_text(encoding="utf-8"))
                j[bad_key] = bad_value
                bad = Path(tmp)/"evidence.json"
                bad.write_text(json.dumps(j),encoding="utf-8")
                with patch.object(g34, "G33", bad):
                    with self.assertRaisesRegex(ValueError, "does not support"):
                        g34.pinned_source()
    def test_do_not_write_in_source_repo(self):
        with self.assertRaisesRegex(ValueError, "outside repository"):
            g34.build(ROOT/"candidate-output")

if __name__ == "__main__":
    unittest.main()
