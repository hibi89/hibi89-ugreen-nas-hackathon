"""G36 functional guarded delegation contract, not vendor certification."""
from pathlib import Path
import re,shlex,unittest
P=Path(__file__).resolve().parents[1]/"docs/submission/checker_inputs"
class G36Tests(unittest.TestCase):
 def test_preserves_g32(self):
  old=(P/"G32_20261026/projectready-nas/SKILL.md").read_text(encoding="utf-8")
  new=(P/"G36_20261026/projectready-nas/SKILL.md").read_text(encoding="utf-8")
  self.assertIn("G32 shell-quoting",old)
  self.assertNotIn("G32 shell-quoting",new)
 def test_two_valid_complete_guard_tasks(self):
  text=(P/"G36_20261026/projectready-nas/SKILL.md").read_text(encoding="utf-8")
  commands=re.findall(r"`(delegate --target (file-agent|document-agent) --instruction '[^`]+')`",text)
  self.assertEqual([name for _,name in commands],["file-agent","document-agent"])
  for command,name in commands:
   parts=shlex.split(command)
   self.assertEqual(parts[:4],["delegate","--target",name,"--instruction"])
   self.assertEqual(len(parts),5)
   task=parts[4]
   for x in ("verify","permission","return","stop","read-only"):
    self.assertIn(x,task.lower())
   self.assertGreater(len(task),550)
   for token in ("syntax-only","example","$FILE_AGENT_INSTRUCTION","$DOCUMENT_AGENT_INSTRUCTION"):
    self.assertNotIn(token,task)
 def test_incomplete_denied_content_never_ready(self):
  text=(P/"G36_20261026/projectready-nas/SKILL.md").read_text(encoding="utf-8")
  for word in ("owner","NOT_CHECKED","waiting_user","CONTENT_NOT_CHECKED","NEEDS_REVIEW",
               "verbatim","same final instruction string","No", "permission", "data"):
   self.assertIn(word,text)
  for token in ("syntax-only example","inert refusal examples","SYNTHETIC EXAMPLE ONLY",
                "No owner-approved folder, checklist","No separately owner-approved exact"):
   self.assertNotIn(token,text)
if __name__=="__main__":unittest.main()
