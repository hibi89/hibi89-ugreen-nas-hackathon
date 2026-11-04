"""G261 non-network owner-scope validation tests with dummy inputs only."""
import copy
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from flowpilot_g261_owner_scope import bind_owner_scope, ScopeRefused, SCHEMA


def req():
    return {"schema":SCHEMA,"mode":"CHECK_DELIVERY",
            "authorized_root":"/volume1/Client_A","required_files":["납품/도면.pdf","report/final.csv"],
            "metadata_approved":True,"scope_authorized":True,
            "allow_symlinks":False,"allow_content_read":False,
            "external_transfer_approved":False}

class G261Tests(unittest.TestCase):
    def test_realistic_unicode_read_scope_is_bound_and_redacted(self):
        result=bind_owner_scope(req())
        self.assertEqual(result["required_file_count"],2)
        self.assertEqual(result["status"],"LOCAL_SCOPE_REQUEST_BOUND_AWAITING_REAL_EXPERT")
        self.assertEqual(len(result["request_sha256"]),64)
        self.assertNotIn("납품",str(result))
        self.assertNotIn("Client_A",str(result))
        self.assertFalse(result["nas_verified"])
        self.assertFalse(result["delegated_instruction_created"])
    def test_deterministic_identity_and_no_content_approval(self):
        a=bind_owner_scope(req());b=bind_owner_scope(req());self.assertEqual(a,b)
        modified=req();modified["required_files"].reverse()
        self.assertNotEqual(a["request_sha256"],bind_owner_scope(modified)["request_sha256"])
        self.assertFalse(a["read_content_approved"])
    def test_unsafe_sources_fail_closed(self):
        for bad in ("../evil", "/etc/passwd", "safe/../../outside", "safe//duplicate", "abc\\def", "name';rm -rf /", "secret/token.txt", "private_key.pem", "file\nname", "safe/./name", "safe/", "safe/na"+chr(96)+"me", "safe/$TOKEN"):
            with self.subTest(file=bad):
                q=req();q["required_files"]=[bad]
                with self.assertRaises(ScopeRefused):bind_owner_scope(q)
    def test_boolean_approvals_are_strict(self):
        for name,value in (("metadata_approved",False),("scope_authorized",False),
                           ("allow_symlinks",True),("allow_content_read",True),
                           ("external_transfer_approved",True),
                           ("metadata_approved","yes"),("allow_symlinks",0)):
            with self.subTest(name=name,value=value):
                q=req();q[name]=value
                with self.assertRaises(ScopeRefused):bind_owner_scope(q)
    def test_bad_modes_and_unknown_keys(self):
        q=req();q["mode"]="EXECUTE_SHELL"
        with self.assertRaises(ScopeRefused):bind_owner_scope(q)
        q=req();q["session_token"]="secret"
        with self.assertRaises(ScopeRefused):bind_owner_scope(q)
    def test_duplicate_and_unbounded_files(self):
        for values in ([],["a"]*2,[str(i) for i in range(41)]):
            q=req();q["required_files"]=values
            with self.assertRaises(ScopeRefused):bind_owner_scope(q)
    def test_root_must_be_absolute_narrow(self):
        for root in ("/","/volume1/..","/volume1//dir","relative","/volume1/","/volume1/.ssh"):
            q=req();q["authorized_root"]=root
            with self.assertRaises(ScopeRefused):bind_owner_scope(q)
if __name__=="__main__":unittest.main()
