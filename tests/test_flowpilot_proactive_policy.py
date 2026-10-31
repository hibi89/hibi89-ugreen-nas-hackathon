"""G119 consented input evaluation with dedup and three/hour maximum."""
import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_proactive_policy import evaluate_tick, new_state

HOT = {"disk_used_percent": 96, "repeated_error_count": 4, "backup_age_hours": 80}


class G119PolicyTests(unittest.TestCase):
    def test_no_consent_leaves_state_unchanged(self):
        state = new_state()
        r = evaluate_tick(HOT, state, 1000)
        self.assertEqual(r["status"], "DISABLED_NO_CONSENT")
        self.assertEqual(r["next_state"], state)
        self.assertFalse(r["nas_polled"])

    def test_two_alerts_per_tick_and_second_tick_global_limit(self):
        a = evaluate_tick(HOT, new_state(), 1000, opted_in=True)
        self.assertEqual(a["proposal_count"], 2)
        self.assertEqual(a["suppressed_count"], 1)
        b = evaluate_tick(HOT, a["next_state"], 1001, opted_in=True)
        self.assertEqual(b["proposal_count"], 1)
        c = evaluate_tick(HOT, b["next_state"], 1002, opted_in=True)
        self.assertEqual(c["proposal_count"], 0)
        self.assertEqual(c["status"], "THROTTLED_OR_DUPLICATE")

    def test_after_cooldown_recovers_without_background_monitor(self):
        a = evaluate_tick(HOT, new_state(), 1000, opted_in=True)
        b = evaluate_tick(HOT, a["next_state"], 4600, opted_in=True)
        self.assertEqual(b["proposal_count"], 2)
        self.assertFalse(b["monitor_started"])
        self.assertFalse(b["actions_executed"])

    def test_revocation_and_backward_time_do_not_modify_state(self):
        a = evaluate_tick(HOT, new_state(), 3000, opted_in=True)
        state = deepcopy(a["next_state"])
        b = evaluate_tick(HOT, state, 3010, opted_in=False)
        self.assertEqual(b["next_state"], state)
        c = evaluate_tick(HOT, state, 2999, opted_in=True)
        self.assertEqual(c["status"], "NON_MONOTONIC_TICK")
        self.assertEqual(c["next_state"], state)

    def test_invalid_telemetry_never_advances_counters(self):
        state = new_state()
        r = evaluate_tick({"disk_used_percent": "huge"}, state, 4000, opted_in=True)
        self.assertEqual(r["status"], "INVALID_TELEMETRY")
        self.assertEqual(r["next_state"], state)

    def test_mutated_or_forged_state_rejected_without_side_effects(self):
        for value in ({"schema": "bad", "last_tick": 0, "recent": []},
                      {"schema": "flowpilot-proactive-policy-v1",
                       "last_tick": 100, "recent": [{"time": 99, "id": "AUTOMATIC_DELETE"}]},
                      [], None):
            r = evaluate_tick(HOT, value, 1000, opted_in=True)
            self.assertEqual(r["status"], "INVALID_STATE_OR_TIME")
            self.assertFalse(r["actions_executed"])

    def test_revoked_consent_does_not_echo_invalid_private_state(self):
        secret = {"private": "owner-secret-key"}
        row = evaluate_tick(HOT, secret, 100, opted_in=False)
        self.assertEqual(row["status"], "DISABLED_NO_CONSENT")
        self.assertNotIn("owner-secret-key", json.dumps(row))
        self.assertEqual(row["next_state"], new_state())

    def test_unhashable_forged_id_fails_closed(self):
        row = evaluate_tick(HOT, {"schema": "flowpilot-proactive-policy-v1",
                                  "last_tick": 300, "recent": [
                                      {"time": 300, "id": ["injected"]}
                                  ]}, 301, opted_in=True)
        self.assertEqual(row["status"], "INVALID_STATE_OR_TIME")

    def test_no_alerts_and_missing_metrics(self):
        r = evaluate_tick({"disk_used_percent": 50}, new_state(), 1000, opted_in=True)
        self.assertEqual(r["status"], "NO_ALERTS")
        self.assertEqual(r["proposal_count"], 0)

    def test_cli_offline_only(self):
        cmd = [sys.executable, str(ROOT/"tools"/"flowpilot_proactive_policy.py"),
               "--telemetry-json", json.dumps(HOT), "--now", "1000", "--opt-in"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        o = json.loads(p.stdout)
        self.assertEqual(o["proposal_count"], 2)
        self.assertFalse(o["notifications_sent"])
        self.assertFalse(o["nas_polled"])


if __name__ == "__main__":
    unittest.main()
