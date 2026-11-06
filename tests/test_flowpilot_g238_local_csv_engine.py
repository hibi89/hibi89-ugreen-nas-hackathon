"""G238 actual LOCAL operator-data bounded CSV workflow, no NAS or network."""
from __future__ import annotations

import csv
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flowpilot_g238_local_csv_engine as engine

GOAL = "customer"
ROWS = b"customer,amount_cents\nalice,125\nbob,300\nalice,275\n"


class LocalCsvWorkflowTests(unittest.TestCase):
    def setUp(self):
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.base = Path(holder.name)
        self.input = self.base / "private-data.csv"
        self.input.write_bytes(ROWS)
        self.plan = engine.preview(str(self.input), GOAL)

    def run_approved(self, **kwargs):
        return engine.execute(str(self.input), GOAL, self.plan["plan_sha256"],
                              engine.READ_ACK, **kwargs)

    def test_preview_zero_stat_open_read_or_write(self):
        with patch.object(engine.os, "open", side_effect=AssertionError("read")):
            result = engine.preview(str(self.input), GOAL)
        self.assertEqual(result, self.plan)
        self.assertFalse(result["input_file_touched"])
        self.assertNotIn(str(self.input), json.dumps(result))

    def test_actual_group_by_and_redacted_proof(self):
        result = self.run_approved()
        self.assertEqual(result["source_rows"], 3)
        self.assertEqual(result["group_count"], 2)
        self.assertEqual([r["total_cents"] for r in
                          result["redacted_group_totals"]], [400, 300])
        self.assertEqual(result["typed_nodes_executed"], list(engine.STEPS))
        self.assertEqual(result["source_sha256"], sha256(ROWS).hexdigest())
        self.assertFalse(result["nas_verified"])
        self.assertEqual(self.input.read_bytes(), ROWS)
        for secret in ("alice", "bob", str(self.input)):
            self.assertNotIn(secret, json.dumps(result))

    def test_different_input_is_actually_aggregated_not_fixed_receipt(self):
        self.input.write_bytes(
            b"customer,amount_cents\nzoe,777\nyan,25\nyan,25\n")
        out = self.run_approved()
        self.assertEqual([r["total_cents"] for r in out["redacted_group_totals"]],
                         [50, 777])
        self.assertEqual(out["source_rows"], 3)

    def test_department_plan_and_run(self):
        self.input.write_bytes(b"department,amount_cents\nops,100\nops,100\nqa,5\n")
        p = engine.preview(str(self.input), "department")
        result = engine.execute(str(self.input), "department",
                                p["plan_sha256"], engine.READ_ACK)
        self.assertEqual(result["group_count"], 2)
        self.assertEqual([r["total_cents"] for r in result["redacted_group_totals"]],
                         [200, 5])

    def test_missing_mismatched_or_forged_approval_never_reads(self):
        for plan, ack in ((None,engine.READ_ACK),
                          (self.plan["plan_sha256"], None),
                          ("0"*64,engine.READ_ACK),
                          (self.plan["plan_sha256"],"APPROVE_NAS"),
                          (True,engine.READ_ACK)):
            with self.subTest(plan=plan),patch.object(engine,"_read_once",
                                                       side_effect=AssertionError("read attempted")):
                with self.assertRaises(engine.LocalCsvRefused):
                    engine.execute(str(self.input), GOAL, plan, ack)

    def test_rejects_malformed_untrusted_csv(self):
        for raw in (
            b"bad,amount_cents\nalice,1\n",
            b"customer,amount_cents\n=cmd,5\n",
            b"customer,amount_cents\nalice,-1\n",
            b"customer,amount_cents\nalice,3O0\n",
            b"customer,amount_cents\nalice,1000001\n",
            b"customer,amount_cents\nalice,1,extra\n",
            b"customer,amount_cents\n",
            b"customer,amount_cents\nalice,1\n\xff",
        ):
            with self.subTest(raw=raw[:30]),self.assertRaises(engine.LocalCsvRefused):
                engine._typed_run(raw, GOAL)

    def test_no_overflow_or_unbounded_group_cardinality(self):
        large = b"customer,amount_cents\n" + b"x,1\n" * 257
        with self.assertRaises(engine.LocalCsvRefused):
            engine._typed_run(large, GOAL)
        groups = b"customer,amount_cents\n" + b"".join(
            f"g{i},1\n".encode("ascii") for i in range(33))
        with self.assertRaises(engine.LocalCsvRefused):
            engine._typed_run(groups, GOAL)

    def test_absolute_path_and_group_allowlist(self):
        for path in ("relative.csv", "../private.csv", "", "/tmp/../secret.csv"):
            with self.subTest(path=path),self.assertRaises(engine.LocalCsvRefused):
                engine.preview(path, GOAL)
        with self.assertRaises(engine.LocalCsvRefused):
            engine.preview(str(self.input), "arbitrary_unsafe_python")

    def test_symlink_and_hardlink_input_denied(self):
        other = self.base / "link.csv"
        try:
            other.symlink_to(self.input)
        except (OSError,NotImplementedError):
            self.skipTest("symlinks require elevated privileges")
        with self.assertRaises(engine.LocalCsvRefused):
            engine.execute(str(other), GOAL,
                           engine.preview(str(other), GOAL)["plan_sha256"],
                           engine.READ_ACK)
        other.unlink()
        if os.name != "nt":
            os.link(self.input,other)
            with self.assertRaises(engine.LocalCsvRefused):
                self.run_approved()

    def test_no_write_implicit_and_separate_export_approval_required(self):
        dest=self.base/"report.csv"
        with self.assertRaises(engine.LocalCsvRefused):
            self.run_approved(export_to=str(dest))
        self.assertFalse(dest.exists())
        out=self.run_approved(export_to=str(dest),
                              export_approval=engine.EXPORT_ACK)
        self.assertTrue(out["report_file_created"])
        with dest.open(newline="",encoding="utf-8") as handle:
            content=list(csv.reader(handle))
        self.assertEqual(content[0],["customer","total_cents","source_rows"])
        self.assertEqual(content[1:], [["alice","400","2"],["bob","300","1"]])
        with self.assertRaises(engine.LocalCsvRefused):
            self.run_approved(export_to=str(dest),
                              export_approval=engine.EXPORT_ACK)
        self.assertEqual(self.input.read_bytes(), ROWS)

    def test_redacted_audit_requires_separate_opt_in_and_is_create_only(self):
        dest=self.base/"audit.json"
        with self.assertRaises(engine.LocalCsvRefused):
            self.run_approved(audit_to=str(dest),audit_approval="yes")
        first=self.run_approved(audit_to=str(dest),
                                audit_approval=engine.AUDIT_ACK)
        recorded=json.loads(dest.read_bytes())
        self.assertEqual(first["receipt_sha256"], recorded["receipt_sha256"])
        self.assertNotIn("alice",dest.read_text())
        with self.assertRaises(engine.LocalCsvRefused):
            self.run_approved(audit_to=str(dest),
                              audit_approval=engine.AUDIT_ACK)

    def test_export_and_audit_in_one_call_refused_before_read(self):
        with patch.object(engine,"_read_once",
                          side_effect=AssertionError("attempted read")):
            with self.assertRaises(engine.LocalCsvRefused):
                self.run_approved(export_to=str(self.base/"a.csv"),
                                  export_approval=engine.EXPORT_ACK,
                                  audit_to=str(self.base/"b.json"),
                                  audit_approval=engine.AUDIT_ACK)

    def test_disallow_output_overwriting_source(self):
        with self.assertRaises(engine.LocalCsvRefused):
            self.run_approved(export_to=str(self.input),
                              export_approval=engine.EXPORT_ACK)
        self.assertEqual(self.input.read_bytes(), ROWS)


    def test_g278_reparse_parent_or_input_refused_before_source_open(self):
        # Cross-platform simulation of Windows junction/reparse metadata:
        # Path.is_symlink() alone cannot guarantee this boundary.
        actual_lstat = Path.lstat
        for flagged in (self.base, self.input):
            with self.subTest(flagged=str(flagged)):
                def synthetic_lstat(path, *args, **kwargs):
                    metadata = actual_lstat(path, *args, **kwargs)
                    if path == flagged:
                        return SimpleNamespace(
                            st_mode=metadata.st_mode, st_size=metadata.st_size,
                            st_nlink=metadata.st_nlink,
                            st_file_attributes=engine.FILE_ATTRIBUTE_REPARSE_POINT)
                    return metadata
                with patch.object(Path, "lstat", synthetic_lstat), \
                     patch.object(engine.os, "open",
                                  side_effect=AssertionError("unexpected input open")):
                    with self.assertRaises(engine.LocalCsvRefused):
                        engine._read_once(self.input)
        self.assertEqual(self.input.read_bytes(), ROWS)

    def test_g278_reparse_output_refused_before_create(self):
        output = self.base / "review-output.csv"
        actual_lstat = Path.lstat
        def synthetic_lstat(path, *args, **kwargs):
            if path == output:
                return SimpleNamespace(st_mode=stat.S_IFREG | 0o600,
                                       st_file_attributes=engine.FILE_ATTRIBUTE_REPARSE_POINT)
            return actual_lstat(path, *args, **kwargs)
        with patch.object(Path, "lstat", synthetic_lstat), \
             patch.object(engine.os, "open",
                          side_effect=AssertionError("unexpected report creation")):
            with self.assertRaises(engine.LocalCsvRefused):
                engine._create_only(str(output), b"safe", self.input)
        self.assertFalse(output.exists())

    def test_preview_vs_run_cli_and_no_secret_log(self):
        src=Path(engine.__file__)
        base=[sys.executable,str(src),"--input",str(self.input),
              "--group-column",GOAL]
        p=subprocess.run(base+["--mode","preview"],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        pre=json.loads(p.stdout)
        self.assertEqual(pre,self.plan)
        denied=subprocess.run(base+["--mode","run"],capture_output=True,text=True)
        self.assertEqual(denied.returncode,2)
        self.assertEqual(json.loads(denied.stdout)["status"],"G238_REFUSED")
        okay=subprocess.run(base+["--mode","run",
            "--plan-sha256",pre["plan_sha256"],"--approval",engine.READ_ACK],
            capture_output=True,text=True)
        self.assertEqual(okay.returncode,0,okay.stderr)
        result=json.loads(okay.stdout)
        self.assertEqual(result["group_count"],2)
        for value in (str(self.input),"alice","bob"):
            self.assertNotIn(value,okay.stdout)


if __name__ == "__main__":
    unittest.main()
