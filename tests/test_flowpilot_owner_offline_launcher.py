"""G152 static guard for standalone PowerShell 5.1 launcher.

The Windows Actions job also executes real PowerShell preflight and refusal.
No actual Uliya Kit, owner artifact, Docker, NAS, or vendor JS in CI.
"""
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "flowpilot_owner_official_offline.ps1"


class G152OfflineLauncherContractTests(unittest.TestCase):
    def test_no_auto_network_clone_or_download(self):
        source = SCRIPT.read_text(encoding="utf-8")
        forbidden = (
            "git clone", "Invoke-WebRequest", "Invoke-RestMethod",
            "Start-BitsTransfer", "DownloadFile(", "curl.exe", "wget.exe",
            "'--download-official-kit'", '"--download-official-kit"',
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_only_explicit_switch_can_enable_vendor_execution(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("[switch]$ExecuteOfficialNativeCode", source)
        self.assertIn("if ($ExecuteOfficialNativeCode) { $runnerArgs += '--execute-official-native-code' }", source)
        self.assertIn("if ($PreflightOnly)", source)
        self.assertIn("EXECUTION_NOT_ALLOWED_DURING_PREFLIGHT", source)

    def test_single_executable_selection_under_multiple_windows_python_installs(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Get-Command 'python' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1", source)
        self.assertIn("Get-Command 'node' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1", source)

    def test_exact_private_pair_and_kit_passing_without_upload(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("'flowpilot_owner_official_oneshot.py'", source)
        self.assertIn("'--folder', $ArtifactFolder, '--official-kit-zip', $OfficialKitZip", source)
        self.assertIn("private_artifacts_uploaded = $false", source)
        self.assertIn("release_gate = 'HOLD'", source)
        self.assertIn("LOCAL_VENDOR_KIT_FILE_MISSING", source)


if __name__ == "__main__":
    unittest.main()
