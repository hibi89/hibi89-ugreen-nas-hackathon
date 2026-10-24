"""G28 safe editorial candidate offline tests."""
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import round1_editorial_release_preview as editor

class G28EditorTests(unittest.TestCase):
    def test_source_and_receipt(self):
        b = editor.verified_input()
        self.assertEqual(editor.digest(b), editor.G22_SHA)
        self.assertIn(b"SYNTHETIC EXAMPLE ONLY", b)

    def test_safe_editorial_change(self):
        base = editor.verified_input()
        changed = editor.editorial_bytes(base)
        self.assertNotEqual(base, changed)
        self.assertNotIn(b"SYNTHETIC EXAMPLE ONLY", changed)
        self.assertNotIn(b"delegate --target", changed)
        self.assertNotIn(editor.STALE.encode("utf-8"), changed)
        self.assertIn(b"separate official checker evidence", changed)
        self.assertIn(b"waiting_user", changed)
        self.assertEqual(editor.digest(base), editor.G22_SHA)

    def test_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, "Wrong G22"):
            editor.editorial_bytes(editor.verified_input()+b"x")

    def test_marker_drift_rejected(self):
        with patch.object(editor,"BEGIN","missing fake marker"):
            with self.assertRaisesRegex(ValueError, "boundaries changed"):
                editor.editorial_bytes(editor.verified_input())

    def test_checker_receipt_tamper_rejected(self):
        obj=json.loads(editor.RECEIPT.read_text(encoding="utf-8"))
        obj["summary"]["warnings"]=1
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"checker.json"
            f.write_text(json.dumps(obj),encoding="utf-8")
            with patch.object(editor,"RECEIPT",f):
                with self.assertRaisesRegex(ValueError, "not matching"):
                    editor.verified_input()

    def test_proposal_limit(self):
        p=editor.editorial_proposal()
        self.assertEqual(len(p["questions"]),10)
        self.assertLessEqual(p["substantive_words"],500)
        self.assertIn("checker evidence for its exact SHA",p["questions"][7]["answer"])

    def test_one_markdown_zip_reproducible(self):
        b=editor.editorial_bytes(editor.verified_input())
        z1=editor.zip_only_skill(b)
        self.assertEqual(z1,editor.zip_only_skill(b))
        with zipfile.ZipFile(io.BytesIO(z1)) as z:
            self.assertEqual(z.namelist(),["projectready-nas/SKILL.md"])
            self.assertEqual(z.read("projectready-nas/SKILL.md"),b)

    def test_no_write_in_repo(self):
        with self.assertRaisesRegex(ValueError,"outside repository"):
            editor.build(ROOT/"candidate")

if __name__=="__main__":
    unittest.main()
