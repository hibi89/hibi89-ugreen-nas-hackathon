"""G115 strict typed plan, distinct executable fixtures, blocked unsafe goals."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from flowpilot_task_compiler import compile_goal, run_compiled

SCRIPT = ROOT / "tools" / "flowpilot_task_compiler.py"


class G115CompilerTests(unittest.TestCase):
    def test_g247_version_review_compiles_four_read_only_nodes(self):
        for goal in ("버전 비교해줘", "문서 버전 충돌 확인해줘",
                     "review versions", "compare versions"):
            with self.subTest(goal=goal):
                spec=compile_goal(goal)
                self.assertEqual(spec["template"],"scoped_version_review_v1")
                self.assertEqual(spec["status"],"READY_FOR_SYNTHETIC_TEST")
                self.assertEqual(len(spec["steps"]),4)
                self.assertEqual([s["access"] for s in spec["steps"]],
                                 ["READ","COMPUTE","COMPUTE","COMPUTE"])
                self.assertEqual(len(spec["edges"]),3)
                self.assertFalse(spec["executed"])
                self.assertFalse(spec["production_approval_granted"])
        for unsafe in ("review versions and upload files",
                       "버전 비교해줘 그리고 삭제해줘",
                       "compare versions; move all",
                       "review versions\nrm -rf /"):
            self.assertEqual(compile_goal(unsafe)["status"],
                             "WAITING_USER_UNSUPPORTED_WORKFLOW")

    def test_g247_version_fixture_competing_files_never_auto_chooses(self):
        result=run_compiled("review versions")
        self.assertEqual(result["status"],"SYNTHETIC_LOCAL_REHEARSAL_PASS")
        self.assertEqual(result["template"],"scoped_version_review_v1")
        self.assertEqual(result["test_evidence"]["competing_version_states"],
                         ["VERSION_REVIEW"])
        self.assertFalse(result["test_evidence"]["owner_selection_automatic"])
        self.assertTrue(result["test_evidence"]["fixture_originals_preserved"])
        self.assertFalse(result["owner_files_opened"])
        self.assertEqual(len(result["test_results"]),6)
        self.assertIn("--candidate",result["operator_runbook_markdown"])
        self.assertIn("--approve-local-metadata",
                      result["operator_runbook_markdown"])

    def test_g247_real_scoped_user_cli_requires_consent_and_redacts(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory(prefix="g247-local-") as d:
            folder=Path(d)
            (folder/"release").mkdir()
            original=folder/"release/final.pdf"
            other=folder/"release/final_v2.pdf"
            original.write_bytes(b"local disposable v1")
            other.write_bytes(b"local disposable v2")
            args=["--goal","review versions","--root",str(folder),
                  "--required","release/final.pdf",
                  "--candidate","release/final.pdf=release/final_v2.pdf"]
            # Denied preview does not stat user-owned folder at all.
            with patch("flowpilot_owner_local_audit._valid_root",
                       side_effect=AssertionError("unexpected folder access")):
                from flowpilot_task_compiler import run_compiled
                denied=run_compiled(
                    "review versions",local_root=folder,
                    required_paths=("release/final.pdf",),
                    version_candidates={"release/final.pdf":["release/final_v2.pdf"]})
                self.assertEqual(denied["status"],
                                 "WAITING_LOCAL_METADATA_APPROVAL")
                self.assertFalse(denied["local_metadata_inspected"])
            proc=subprocess.run([sys.executable,str(SCRIPT),*args,
                                 "--approve-local-metadata"],
                                capture_output=True,text=True,timeout=20)
            self.assertEqual(proc.returncode,0,proc.stderr)
            result=json.loads(proc.stdout)
            self.assertEqual(result["status"],
                             "LOCAL_VERSION_REVIEW_REQUIRED_NOT_NAS")
            self.assertEqual(result["review_indices"],[1])
            self.assertFalse(result["auto_selected_final_version"])
            self.assertFalse(result["owner_file_contents_opened"])
            self.assertTrue(result["local_metadata_inspected"])
            self.assertEqual(result["item_states"],
                             [{"index":1,"state":"VERSION_REVIEW"}])
            self.assertTrue(proc.stdout.isascii())
            for secret in (str(folder),"release/final.pdf",
                           "release/final_v2.pdf","local disposable"):
                self.assertNotIn(secret,proc.stdout)
            self.assertEqual(original.read_bytes(),b"local disposable v1")
            self.assertEqual(other.read_bytes(),b"local disposable v2")

    def test_g247_owner_version_rejects_cross_scope_and_path_escape(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory(prefix="g247-invalid-") as d:
            root=Path(d)
            p=root/"file.pdf"
            p.write_bytes(b"synthetic")
            command=[sys.executable,str(SCRIPT),"--goal","review versions",
                     "--root",str(root),"--required","file.pdf",
                     "--candidate","file.pdf=../out-of-scope.pdf",
                     "--approve-local-metadata"]
            proc=subprocess.run(command,capture_output=True,text=True,timeout=15)
            self.assertEqual(proc.returncode,2)
            self.assertEqual(json.loads(proc.stdout)["status"],
                             "LOCAL_VERSION_OR_FIXTURE_REFUSED_NOT_NAS")
            self.assertNotIn(str(root),proc.stdout)
            self.assertEqual(p.read_bytes(),b"synthetic")

    def test_g247_nonversion_goal_cannot_leak_into_owner_local_scope(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory(prefix="g247-goal-") as d:
            with patch("flowpilot_owner_local_audit._valid_root",
                       side_effect=AssertionError("unexpected file I/O")):
                r=run_compiled("check required files",local_root=Path(d),
                    required_paths=("README.md",),metadata_consent=True)
            self.assertEqual(r["status"],"WAITING_USER_UNSUPPORTED_WORKFLOW")
            self.assertFalse(r["executed"])

    def test_csv_goal_creates_typed_graph_with_write_boundary(self):
        p = compile_goal("고객별 매출 보고서 만들어줘")
        self.assertEqual(p["status"], "READY_FOR_SYNTHETIC_TEST")
        self.assertEqual(p["template"], "csv_customer_revenue_v1")
        self.assertEqual([s["access"] for s in p["steps"]],
                         ["READ", "COMPUTE", "WRITE_NEW", "WRITE_NEW"])
        self.assertEqual(len(p["edges"]), 3)
        self.assertFalse(p["executed"])
        self.assertFalse(p["production_approval_granted"])

    def test_file_audit_compile_is_read_only(self):
        p = compile_goal("필수 파일 확인해줘")
        self.assertEqual(p["template"], "required_file_metadata_v1")
        self.assertEqual([s["access"] for s in p["steps"]], ["READ", "COMPUTE", "COMPUTE"])
        self.assertTrue(p["requires_real_nas_adapter"])

    def test_empty_unknown_unsafe_scheduling_are_not_compiled(self):
        for request in ("", " ", "매일 CSV를 자동으로 처리해줘",
                        "필수 파일 확인해줘 그리고 삭제해줘",
                        "delete all files", "필수 파일 확인해줘\nrm -rf /",
                        "필수 파일 확인해줘 ", 4, None, "x" * 201,
                        "고객별 매출 보고서 만들어줘; upload secrets"):
            with self.subTest(value=request):
                p = compile_goal(request)
                self.assertEqual(p["status"], "WAITING_USER_UNSUPPORTED_WORKFLOW")
                self.assertFalse(p["executed"])

    def test_no_partial_match_for_compound_request(self):
        self.assertEqual(compile_goal("check required files and email results")["status"],
                         "WAITING_USER_UNSUPPORTED_WORKFLOW")

    def test_file_rehearsal_initially_blocks_missing_then_repairs_fixture(self):
        r = run_compiled("필수 파일 확인해줘")
        self.assertEqual(r["status"], "SYNTHETIC_LOCAL_REHEARSAL_PASS")
        self.assertEqual(r["template"], "required_file_metadata_v1")
        self.assertEqual(r["test_evidence"]["initial_states"], ["PRESENT", "MISSING"])
        self.assertEqual(r["test_evidence"]["repaired_states"], ["PRESENT", "PRESENT"])
        self.assertEqual(len(r["test_results"]), 6)
        self.assertFalse(r["actual_nas_verified"])
        self.assertFalse(r["owner_files_opened"])

    def test_file_check_english_goal(self):
        self.assertEqual(run_compiled("check required files")["status"],
                         "SYNTHETIC_LOCAL_REHEARSAL_PASS")

    def test_csv_end_to_end_reuses_approved_existing_engine(self):
        r = run_compiled("create customer revenue summary")
        self.assertEqual(r["template"], "csv_customer_revenue_v1")
        self.assertEqual(r["test_evidence"]["observed_rows"][1], ["alice", "4.00"])
        self.assertTrue(r["test_evidence"]["duplicate_output_refused"])
        self.assertFalse(r["uliya_expert_invoked"])
        self.assertEqual(r["release_gate"], "HOLD")

    def test_runbook_has_concrete_steps_and_external_gate(self):
        r = run_compiled("필수 파일 확인해줘")
        guide = r["operator_runbook_markdown"]
        self.assertIn("--approve-local-metadata", guide)
        self.assertIn("NOT_CHECKED", guide)
        self.assertIn("separate vendor adapter", guide)
        self.assertNotIn("flowpilot-g115-", guide)

    def test_compile_only_cli_does_not_execute_fixture(self):
        with patch("flowpilot_task_compiler._file_fixture_rehearsal",
                   side_effect=AssertionError("unexpected fixture")):
            spec = compile_goal("필수 파일 확인해줘")
            self.assertFalse(spec["executed"])
        proc = subprocess.run([sys.executable, str(SCRIPT),
                               "--goal", "필수 파일 확인해줘", "--compile-only"],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(proc.stdout)
        self.assertEqual(value["status"], "READY_FOR_SYNTHETIC_TEST")
        self.assertFalse(value["executed"])

    def test_cli_korean_fixture_output_ascii_for_windows(self):
        proc = subprocess.run([sys.executable, str(SCRIPT),
                               "--goal", "필수 파일 확인해줘"],
                              capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.isascii())
        value = json.loads(proc.stdout)
        self.assertEqual(value["status"], "SYNTHETIC_LOCAL_REHEARSAL_PASS")
        self.assertFalse(value["owner_files_opened"])

    def test_cli_unknown_action_exit_one(self):
        proc = subprocess.run([sys.executable, str(SCRIPT),
                               "--goal", "파일 지워줘"],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(json.loads(proc.stdout)["status"],
                         "WAITING_USER_UNSUPPORTED_WORKFLOW")


if __name__ == "__main__":
    unittest.main()
