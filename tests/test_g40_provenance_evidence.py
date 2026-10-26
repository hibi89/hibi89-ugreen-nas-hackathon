"""G40 separate evidence levels: approved ancestry is not inferred from SHA."""
import copy, hashlib, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"tools"))
import g40_provenance_evidence as g

class G40AuditTests(unittest.TestCase):
 def fixture(self):
  x=b"old";y=b"new"
  a={"status":"static-pass","summary":{"errors":0,"warnings":0,"info":0},
     "files":[{"sha256":hashlib.sha256(x).hexdigest(),"path":"SKILL.md"}]}
  b={"checker_status":"static-pass","checker_exit":0,
    "source_sha256":hashlib.sha256(y).hexdigest(),"source_bytes":3,
    "summary":{"errors":0,"warnings":0,"info":0},"checker_run_id":40311253113,"nas_runtime":"NOT_RUN"}
  c={"source_sha256":hashlib.sha256(y).hexdigest(),
     "zip":{"contained_skill_sha256":hashlib.sha256(y).hexdigest()},
     "pdf":{"sha256":"d5d1bf9383d9f7d811f2e8f30b649a41e2b2b382ce3d8ae4f60c75e917874936"},
     "workflow":{"artifact_id":12644844524},"limitations":{"devpost":"NOT_SUBMITTED"}}
  d={"official_pinned_archive":{"sha256":"cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3",
      "checked_file_count":26,"license_candidate_file_count":0},
     "actual_vendor_kit_license":"NOT_IDENTIFIED_FROM_PINNED_ARCHIVE_OR_LINKED_PUBLIC_TERMS"}
  return x,y,a,b,c,d
 def patch_shas(self,old,new):
  previous=(g.REVIEW_SHA,g.G36_SHA)
  g.REVIEW_SHA=hashlib.sha256(old).hexdigest()
  g.G36_SHA=hashlib.sha256(new).hexdigest()
  return previous
 def restore(self,pair):
  g.REVIEW_SHA,g.G36_SHA=pair
 def test_no_source_forgery(self):
  old,new,a,b,c,d=self.fixture()
  old_sha=g.REVIEW_SHA
  with self.assertRaisesRegex(ValueError,"G20 review source drift"):
   g.assess(old,new,a,b,c,d)
  self.assertEqual(g.REVIEW_SHA,old_sha)
 def test_no_checker_forgery(self):
  old,new,a,b,c,d=self.fixture()
  old_pair=self.patch_shas(old,b"x"*14522)
  try:
   with self.assertRaisesRegex(ValueError,"G36 exact first-party checker source drift"):
    g.assess(old,new,a,b,c,d)
  finally:self.restore(old_pair)
 def test_g20_false_pass_rejected(self):
  old,new,a,b,c,d=self.fixture()
  current=b"n"*14522
  previous=self.patch_shas(old,current)
  b.update(source_sha256=g.G36_SHA,source_bytes=14522)
  c.update(source_sha256=g.G36_SHA)
  c["zip"]["contained_skill_sha256"]=g.G36_SHA
  a["summary"]["warnings"]=1
  try:
   with self.assertRaisesRegex(ValueError,"Review commit checker JSON"):
    g.assess(old,current,a,b,c,d)
  finally:self.restore(previous)
 def test_no_owner_approval_even_with_valid_evidence(self):
  old,new,a,b,c,d=self.fixture()
  current=b"n"*14522
  previous=self.patch_shas(old,current)
  b.update(source_sha256=g.G36_SHA,source_bytes=14522)
  c.update(source_sha256=g.G36_SHA)
  c["zip"]["contained_skill_sha256"]=g.G36_SHA
  try:
   proof=g.assess(old,current,a,b,c,d)
   self.assertTrue(proof["source_git_bytes_verified"])
   self.assertFalse(proof["creator_run_locally_replayed"])
   self.assertFalse(proof["g39_license_grant_established"])
   self.assertFalse(proof["user_signed_submission"])
   self.assertEqual(proof["release_decision"],"HOLD_LICENSE_CREATOR_PROVENANCE_AND_ENTRANT_SIGNOFF")
  finally:self.restore(previous)
 def test_license_metadata_cannot_approve(self):
  old,new,a,b,c,d=self.fixture()
  current=b"n"*14522
  previous=self.patch_shas(old,current)
  b.update(source_sha256=g.G36_SHA,source_bytes=14522)
  c.update(source_sha256=g.G36_SHA)
  c["zip"]["contained_skill_sha256"]=g.G36_SHA
  d["official_pinned_archive"]["license_candidate_file_count"]=1
  try:
   with self.assertRaisesRegex(ValueError,"license inventory drift"):
    g.assess(old,current,a,b,c,d)
  finally:self.restore(previous)

if __name__=="__main__":unittest.main()
