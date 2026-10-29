"""Focused offline tests for the static FlowPilot Command Center."""
import json
import tempfile
import unittest
from pathlib import Path

from flowpilot_command_center import render_dashboard, main


class DashboardTests(unittest.TestCase):
    def test_approval_preview_is_not_execution(self):
        page = render_dashboard({
            "status": "WAITING_EXECUTION_APPROVAL",
            "request": {"missing_inputs": []},
            "workflow_graph": {"nodes": [{"type": "csv_read", "label": "Read CSV"}]},
        })
        self.assertIn("Awaiting explicit approval", page)
        self.assertIn("Read CSV", page)
        self.assertIn("NAS UNVERIFIED", page)
        self.assertNotIn("Local report created", page)

    def test_completed_is_only_local(self):
        page = render_dashboard({"status": "LOCAL_REPORT_CREATED_NOT_NAS", "executed": True})
        self.assertIn("Local report created", page)
        self.assertIn("NOT VERIFIED", page)

    def test_html_escaping(self):
        page = render_dashboard({
            "status": "<script>alert(1)</script>",
            "workflow_graph": {"nodes": [{"label": "<img src=x onerror=alert(1)>", "type": "csv_read"}]},
        })
        self.assertNotIn("<script>", page)
        self.assertNotIn("<img src=", page)
        self.assertIn("&lt;img", page)

    def test_file_creation_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d) / "in.json", Path(d) / "out.html"
            inp.write_text(json.dumps({"status": "WAITING_USER"}), encoding="utf-8")
            self.assertEqual(main(["--input", str(inp), "--output", str(out)]), 0)
            self.assertEqual(main(["--input", str(inp), "--output", str(out)]), 2)

    def test_invalid_payload(self):
        with self.assertRaises(ValueError):
            render_dashboard([])


if __name__ == "__main__":
    unittest.main()
