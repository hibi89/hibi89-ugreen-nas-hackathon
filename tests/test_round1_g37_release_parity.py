"""G37: exact G36 official static source and G37 release-preview parity."""
from __future__ import annotations
import io, json, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import round1_g37_release_parity as g37

class G37Tests(unittest.TestCase):
    def test_exact_authorized_file_and_first_party_receipt(self):
        raw=g37.pinned_source()
        self.assertEqual(g37.digest(raw),g37.G36_SHA)
        self.assertEqual(len(raw),14522)
    def test_staged_pdf_answers_and_disclosures(self):
        p=g37.staged_proposal()
        self.assertEqual(len(p["questions"]),10)
        self.assertLessEqual(p["substantive_words"],500)
        self.assertIn("revised G36 Skill passed",p["questions"][7]["answer"])
        self.assertNotIn("No official Uliya validator",p["questions"][7]["answer"])
        self.assertEqual(p["proof_status"]["official_validator"],"G36_EXACT_SHA_FIRST_PARTY_STATIC_PASS")
        self.assertEqual(p["proof_status"]["devpost"],"NOT_SUBMITTED")
        self.assertEqual(p["proof_status"]["nas"],"NOT_RUN")
    def test_one_markdown_zip_and_deterministic_bytes(self):
        from round1_official_creator_preview import zip_only_skill
        source=g37.pinned_source()
        blob=zip_only_skill(source)
        self.assertEqual(blob,zip_only_skill(source))
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            self.assertEqual(z.namelist(),["projectready-nas/SKILL.md"])
            self.assertEqual(z.read("projectready-nas/SKILL.md"),source)
    def test_refuses_changed_skill(self):
        with tempfile.TemporaryDirectory() as td:
            changed=Path(td)/"SKILL.md"
            changed.write_bytes(g37.pinned_source()+b"x")
            with patch.object(g37,"G36",changed):
                with self.assertRaisesRegex(ValueError,"SHA/size changed"):
                    g37.pinned_source()
    def test_refuses_tampered_receipt(self):
        for field,val in (("checker_status","not-uploadable"),
                          ("checker_exit",1),
                          ("source_sha256","a"*64),
                          ("checker_run_id",-1),
                          ("summary",{"errors":0,"warnings":1,"info":0}),
                          ("source_sha_before_after_equal",False)):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
                content=json.loads(g37.G36_EVIDENCE.read_text())
                content[field]=val
                bad=Path(td)/"receipt.json"
                bad.write_text(json.dumps(content))
                with patch.object(g37,"G36_EVIDENCE",bad):
                    with self.assertRaisesRegex(ValueError,"does not support"):
                        g37.pinned_source()
    def test_never_write_source_repo(self):
        with self.assertRaisesRegex(ValueError,"outside repository"):
            g37.build(ROOT/"G37-output")
if __name__=="__main__":
    unittest.main()
