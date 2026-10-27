"""G50 local ZIP composition regression; no external resources."""
import io,sys,unittest,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from flowpilot_package_audit import audit_zip_bytes,EXPECTED_MEMBER
SOURCE=b'---\nname: flowpilot-nas\n---\n# Goal\nRead-only synthetic skill.\n'

def make(entries):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for name,raw in entries:z.writestr(name,raw)
    return b.getvalue()

class G50ZipAudit(unittest.TestCase):
    def test_exact_one_markdown_only(self):
        result=audit_zip_bytes(make([(EXPECTED_MEMBER,SOURCE)]),SOURCE)
        self.assertTrue(result['source_exact_match'])
        self.assertEqual(result['official_uliya_toolkit_files'],0)
        self.assertFalse(result['legal_rights_released'])

    def test_reject_extra_vendor_source(self):
        with self.assertRaises(ValueError):audit_zip_bytes(make([(EXPECTED_MEMBER,SOURCE),('vendor/sdk/cli.py',b'evil')]),SOURCE)

    def test_reject_script(self):
        with self.assertRaises(ValueError):audit_zip_bytes(make([(EXPECTED_MEMBER,SOURCE),('run.sh',b'noop')]),SOURCE)

    def test_source_mismatch_rejected(self):
        with self.assertRaises(ValueError):audit_zip_bytes(make([(EXPECTED_MEMBER,SOURCE+b'x')]),SOURCE)

    def test_reject_wrong_folder(self):
        with self.assertRaises(ValueError):audit_zip_bytes(make([('different/SKILL.md',SOURCE)]),SOURCE)

    def test_reject_invalid_skill_heading(self):
        with self.assertRaises(ValueError):audit_zip_bytes(make([(EXPECTED_MEMBER,b'NOT A SKILL')]),b'NOT A SKILL')

if __name__=='__main__':unittest.main()
