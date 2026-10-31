"""G117 opt-in, read-only proactive signal proposal tests."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_proactive_advisor import advise_local


class G117AdvisorTests(unittest.TestCase):
    def test_consent_absent_defaults_no_access_no_suggestions(self):
        p = advise_local({"disk_used_percent": 97})
        self.assertEqual(p["status"], "DISABLED_NO_CONSENT")
        self.assertFalse(p["nas_polled"])
        self.assertEqual(p["suggestions"], [])

    def test_three_distinct_thresholds_and_no_autofix(self):
        p = advise_local({"disk_used_percent": 95, "repeated_error_count": 3,
                          "backup_age_hours": 72}, opt_in=True)
        self.assertEqual(p["status"], "SUGGESTIONS_READY")
        self.assertEqual(p["suggestion_count"], 3)
        self.assertFalse(p["actions_executed"])
        self.assertTrue(all(s["requires_explicit_user_approval_to_act"]
                            for s in p["suggestions"]))

    def test_below_threshold_does_not_alarm(self):
        p = advise_local({"disk_used_percent": 89, "repeated_error_count": 2,
                          "backup_age_hours": 71}, opt_in=True)
        self.assertEqual(p["status"], "NO_ALERTS_IN_SUPPLIED_DATA")

    def test_missing_metrics_not_checked(self):
        p = advise_local({"disk_used_percent": 90}, opt_in=True)
        self.assertEqual(p["missing_inputs_not_checked"],
                         ["backup_age_hours", "repeated_error_count"])
        self.assertEqual(p["suggestion_count"], 1)

    def test_untrusted_fields_rejected_without_echo(self):
        for r in ({"customer_path": "secret"}, {"disk_used_percent": 200},
                  {"disk_used_percent": -1}, {"disk_used_percent": True},
                  {"repeated_error_count": "99"}, {"backup_age_hours": 100000},
                  {}, [], None):
            with self.subTest(r=r):
                p = advise_local(r, opt_in=True)
                self.assertEqual(p["status"], "INVALID_TELEMETRY")
                self.assertEqual(p["suggestions"], [])
                self.assertNotIn("secret", json.dumps(p))

    def test_invalid_consent_rejected(self):
        self.assertEqual(advise_local({}, opt_in="yes")["status"], "INVALID_CONSENT")

    def test_cli_synthetic_demo(self):
        cmd = [sys.executable, str(ROOT/"tools"/"flowpilot_proactive_advisor.py"),
               "--telemetry-json", '{"disk_used_percent":95,"repeated_error_count":4}',
               "--opt-in"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertEqual(r["suggestion_count"], 2)
        self.assertFalse(r["background_service_started"])
        self.assertFalse(r["nas_polled"])
        self.assertFalse(r["external_notifications_sent"])


if __name__ == "__main__":
    unittest.main()
