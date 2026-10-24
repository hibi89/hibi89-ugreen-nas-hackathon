"""Fixture-only tests for parameter matrix; no real SDK or NAS."""
import hashlib,io,json,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from sdk_parameter_matrix import matrix,identifier
from sdk_action_contract_digest import SELECTION,SOURCE
from inspect_official_sdk import UnsafePackage

def fake(edit=None):
    groups=[]
    for cli,names in SELECTION.items():
        acts=[{"name":name,"parameters":[{"name":"path","type":"string","required":True,
                "repeatable":False,"description":"SENSITIVE_NOT_FOR_LOG"}],
                "effect":"read","approval":"none",
                "permissions":{"knowledgeStatus":"unknown"},
                "errorCodes":{"knowledgeStatus":"unknown"}} for name in names]
        groups.append({"name":cli,"agent":"fake-agent","actions":acts})
    c={"clis":groups}
    if edit:edit(c)
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:z.writestr(SOURCE,json.dumps(c))
    data=out.getvalue()
    return data,hashlib.sha256(data).hexdigest()

class MatrixTest(unittest.TestCase):
    def test_nine_action_names_not_runtime(self):
        data,sha=fake();result=matrix(data,sha)
        self.assertEqual(result["action_count"],9)
        self.assertFalse(result["live_nas_verified"])
        self.assertEqual(result["actions"][0]["parameters"][0]["type"],"string")
        self.assertNotIn("SENSITIVE_NOT_FOR_LOG",str(result))
    def test_reject_unpinned(self):
        data,_=fake()
        with self.assertRaises(UnsafePackage):matrix(data)
    def test_reject_missing_action(self):
        data,sha=fake(lambda x:x["clis"][0]["actions"].pop())
        with self.assertRaises(UnsafePackage):matrix(data,sha)
    def test_reject_required_not_bool(self):
        def change(c):c["clis"][0]["actions"][0]["parameters"][0]["required"]="yes"
        data,sha=fake(change)
        with self.assertRaises(UnsafePackage):matrix(data,sha)
    def test_reject_unsafe_param_name(self):
        def change(c):c["clis"][0]["actions"][0]["parameters"][0]["name"]="$(curl unauthorized)"
        data,sha=fake(change)
        with self.assertRaises(UnsafePackage):matrix(data,sha)
    def test_unsafe_identifier_redacted(self):
        self.assertIsNone(identifier("SECRET=$TOKEN"))
    def test_optional_repeatable_null(self):
        def change(c):del c["clis"][0]["actions"][0]["parameters"][0]["repeatable"]
        data,sha=fake(change)
        self.assertTrue(any(p["repeatable"] is None for r in matrix(data,sha)["actions"] for p in r["parameters"]))
if __name__=="__main__":unittest.main()
