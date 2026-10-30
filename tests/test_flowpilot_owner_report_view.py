"""Static safe export contract checks; no browser or customer file access."""
from __future__ import annotations

from pathlib import Path
import unittest

from tools.flowpilot_four_source_local_ui import HTML


class RedactedLocalReportViewTests(unittest.TestCase):
    def test_both_download_controls_present_and_initially_disabled(self):
        for id in ("ownerExport", "ownerPrint"):
            self.assertIn(f'id="{id}" disabled', HTML)

    def test_printable_report_reuses_only_safe_owner_result(self):
        self.assertIn("ownerReport.stage_results", HTML)
        self.assertIn("escapeHtml(stage.action)", HTML)
        self.assertIn("flowpilot-local-printable-report.html", HTML)
        self.assertIn("NOT NAS EVIDENCE", HTML)
        self.assertNotIn("ownerRoot.value+", HTML)
        self.assertNotIn("ownerRequired.value+", HTML)

    def test_json_export_has_one_js_escape_for_valid_newline(self):
        line = next(line for line in HTML.splitlines()
                    if "downloadReport(JSON.stringify(ownerReport" in line)
        self.assertIn(r'"\n"', line)
        self.assertNotIn(r'"\\n"', line)

    def test_change_invalidates_both_download_buttons(self):
        self.assertIn('document.getElementById("ownerPrint").disabled=true', HTML)
        self.assertIn('document.getElementById("ownerExport").disabled=true', HTML)
        self.assertIn("if(revision!==ownerRevision)return", HTML)


if __name__ == "__main__":
    unittest.main()
