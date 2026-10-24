"""G22 isolated official Creator preview - no remote NAS or official tool execution."""
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
import round1_official_creator_preview as creator

class CreatorPreviewTests(unittest.TestCase):
    def test_exact_one_file_zip(self):
        skill=b"---\nname: projectready-nas\n---\n# Goal\n"
        archive=creator.zip_only_skill(skill)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            self.assertEqual(["projectready-nas/SKILL.md"],z.namelist())
            self.assertEqual(skill,z.read("projectready-nas/SKILL.md"))
            self.assertEqual(1,len(z.infolist()))

    def test_candidate_disclosure_and_original_unchanged(self):
        source=b"---\nname: projectready-nas\n---\n# Goal\nDo not write.\n"
        original=bytes(source)
        candidate=creator.candidate_bytes(source).decode("utf-8")
        self.assertEqual(original,source)
        self.assertIn("AI development tools:",candidate)
        self.assertIn("official UGREEN Uliya Skill Creation Tool",candidate)
        self.assertIn("local",candidate)
        self.assertIn("pending entrant verification",candidate)
        self.assertIn("not authorized for publication",candidate)

    def test_proposal_updated_without_mutating_canonical(self):
        canonical=json.loads(creator.JSON_PATH.read_text(encoding="utf-8"))
        new=creator.creator_proposal()
        self.assertEqual(10,len(new["questions"]))
        self.assertIn("official UGOS Skill Creation Tool",new["questions"][7]["answer"])
        self.assertIn("No registered Agent",new["questions"][7]["answer"])
        self.assertEqual("NOT_RUN",new["proof_status"]["official_validator"])
        self.assertEqual("NOT_RUN",new["proof_status"]["nas"])
        self.assertEqual("NOT_SUBMITTED",new["proof_status"]["devpost"])
        self.assertLessEqual(new["substantive_words"],500)
        self.assertNotEqual(canonical["questions"][7]["answer"],new["questions"][7]["answer"])

    def test_pin_fails_modified_source_and_checker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"projectready-nas"
            root.mkdir()
            skill=root/"SKILL.md"
            check=Path(tmp)/"checker.json"
            skill.write_text("---\nname: projectready-nas\n---\n# Goal\nOriginal.\n",encoding="utf-8")
            check.write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"pinned SHA256"):
                creator.verified_creator_source(skill,check)
            with patch.object(creator,"SKILL_SHA256",creator.digest(skill.read_bytes())):
                with self.assertRaisesRegex(ValueError,"checker JSON"):
                    creator.verified_creator_source(skill,check)

    def test_checker_must_match_status_and_exact_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"projectready-nas";root.mkdir()
            skill=root/"SKILL.md";skill.write_text("---\nname: projectready-nas\n---\n# Goal\n",encoding="utf-8")
            h=creator.digest(skill.read_bytes())
            checker=Path(tmp)/"checker.json"
            check={"status":"static-pass","summary":{"errors":0,"warnings":1,"info":0},
                   "files":[{"path":"SKILL.md","sha256":h}]}
            checker.write_text(json.dumps(check),encoding="utf-8")
            with patch.object(creator,"SKILL_SHA256",h),patch.object(creator,"CHECK_JSON_SHA256",creator.digest(checker.read_bytes())):
                with self.assertRaisesRegex(ValueError,"does not agree"):
                    creator.verified_creator_source(skill,checker)

if __name__ == "__main__":
    unittest.main()
