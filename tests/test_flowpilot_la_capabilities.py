"""Self-contained capability boundary tests, no LA runtime or NAS required."""
import unittest
from flowpilot_la_capabilities import assess_la_compatibility, HAE_LEGACY_OPS


def graph(n=2):
    nodes = [dict(id=f"read_{i+1}", type="csv_read") for i in range(n)]
    nodes += [dict(id="aggregate", type="decimal_group_sum"),
              dict(id="write", type="csv_write_new"),
              dict(id="audit", type="sqlite_audit")]
    edges = [dict(**{"from": f"read_{i+1}", "to": "aggregate"}) for i in range(n)]
    edges += [dict(**{"from": "aggregate", "to": "write"}),
              dict(**{"from": "write", "to": "audit"})]
    return dict(schema="flowpilot-local-workflow-graph-v1", nodes=nodes, edges=edges,
                approval_required=True, execution_performed=False)


class CompatibilityTests(unittest.TestCase):
    def test_hae_legacy_does_not_support_aggregate_graph(self):
        row = assess_la_compatibility(graph())
        self.assertEqual(row["status"], "BLOCKED_MISSING_CAPABILITIES")
        self.assertEqual(row["missing_operations"],
                         ["csv_write_new", "decimal_group_sum", "sqlite_audit"])
        self.assertFalse(row["execution_allowed"])
        self.assertFalse(row["actual_la_engine_invoked"])

    def test_declared_full_support_still_is_not_verified(self):
        declared = HAE_LEGACY_OPS | frozenset({"decimal_group_sum", "csv_write_new", "sqlite_audit"})
        row = assess_la_compatibility(graph(), declared_ops=declared)
        self.assertEqual(row["status"], "DECLARED_COMPATIBLE_UNVERIFIED")
        self.assertFalse(row["execution_allowed"])
        self.assertFalse(row["actual_la_integration_verified"])

    def test_reject_unknown_type(self):
        g = graph()
        g["nodes"][1]["type"] = "shell_exec"
        with self.assertRaises(ValueError):
            assess_la_compatibility(g)

    def test_reject_bad_edge(self):
        g = graph()
        g["edges"].append({"from": "read_1", "to": "audit"})
        with self.assertRaises(ValueError):
            assess_la_compatibility(g)

    def test_reject_approval_bypass(self):
        g = graph()
        g["approval_required"] = False
        with self.assertRaises(ValueError):
            assess_la_compatibility(g)

    def test_reject_duplicate_identifiers(self):
        g = graph()
        g["nodes"][1]["id"] = "read_1"
        with self.assertRaises(ValueError):
            assess_la_compatibility(g)

    def test_reject_capability_string(self):
        with self.assertRaises(ValueError):
            assess_la_compatibility(graph(), declared_ops="csv_read")

    def test_source_does_not_claim_native_la(self):
        row = assess_la_compatibility(graph(1))
        self.assertEqual(row["hae_compatibility_ir"], "axflow.ir.v0")
        self.assertIn("LOCAL_CSV", row["fallback"])


if __name__ == "__main__":
    unittest.main()
