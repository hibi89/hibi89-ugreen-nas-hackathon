"""Check local acceptance dashboard cannot falsely claim 4 PASS / NAS proof."""
from __future__ import annotations

import shutil
import subprocess
import unittest

from tools.flowpilot_four_source_local_ui import HTML


class AcceptanceDashboardContract(unittest.TestCase):
    def test_dashboard_has_four_explicit_local_stage_cards(self):
        for code in ("REAL_OS_LSTAT_1_TO_3_INTENTS",
                     "GENERATED_CSV_AGGREGATION_AND_SQLITE",
                     "OWNER_METADATA_CONSENT_AND_LSTAT",
                     "OWNER_CSV_CONTENT_CONSENT_SQLITE_REPORT"):
            self.assertIn(code, HTML)
        self.assertIn('id="acceptanceCards"', HTML)
        self.assertIn("4 / 4 LOCAL checks PASSED", HTML)
        self.assertIn("NOT NAS or Uliya proof", HTML)

    def test_pass_requires_exact_safe_synthetic_evidence(self):
        for fragment in ("outcome.passed===4", "outcome.failed===0",
                         "outcome.actual_nas_verified===false",
                         "outcome.generated_disposable_test_data_only===true",
                         'r.status==="PASS_SYNTHETIC"',
                         "rows.length===4", "rows.every"):
            self.assertIn(fragment, HTML)

    def test_render_uses_textcontent_not_raw_untrusted_html(self):
        self.assertIn("result.textContent=", HTML)
        self.assertIn("card.append(title,result)", HTML)
        self.assertNotIn("cards.innerHTML", HTML)

    def test_embedded_javascript_syntax_with_node_when_available(self):
        node=shutil.which("node")
        if not node:
            self.skipTest("Node is not installed here")
        js=HTML.split("<script>",1)[1].split("</script>",1)[0]
        # The session token is an ordinary escaped JS string placeholder.
        result=subprocess.run([node,"--check"],input=js,text=True,
                              capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == "__main__":
    unittest.main()
