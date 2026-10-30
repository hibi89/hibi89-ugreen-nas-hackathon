# UGREEN FlowPilot safe one-command LOCAL verification. No NAS, customer DB, API or upload.
param(
  [ValidateSet("smoke", "g88", "full")][string]$Mode = "smoke",
  [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$dest = Join-Path ([System.IO.Path]::GetTempPath()) "ugreen-flowpilot-verify"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$time = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $dest ("verify-" + $time + "-" + $PID + ".log")
$summary = Join-Path $dest ("verify-" + $time + "-" + $PID + ".json")
$sha = "UNAVAILABLE"
$pythonVersion = "UNAVAILABLE"
$exitCode = 1
$status = "FAIL"
$started = [DateTime]::UtcNow
try {
  Push-Location $repo
  try {
    if (Get-Command git -ErrorAction SilentlyContinue) {
      $sha = (& git rev-parse HEAD 2>$null | Out-String).Trim()
      if ($LASTEXITCODE -ne 0) { $sha = "UNAVAILABLE" }
    }
    $pythonVersion = (& $Python --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Python not available" }
    $testPattern = switch ($Mode) {
      "smoke" { "test_flowpilot_goal_preview.py" }
      "g88" { "test_flowpilot_multi_read_review.py" }
      "full" { "test_*.py" }
    }
    # Windows PowerShell 5.1 turns native stderr into error records.
    # unittest -v writes normal progress on stderr; Stop would misclassify it
    # as a runner exception with exit code 2, even when all tests pass.
    # Scope this to the Python process and preserve its actual exit code.
    $previousErrorActionPreference = $ErrorActionPreference
    try {
      $ErrorActionPreference = "Continue"
      & $Python -m unittest discover -s tests -p $testPattern -v 2>&1 |
        Tee-Object -FilePath $log | Out-Null
      $exitCode = $LASTEXITCODE
    } finally {
      $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -eq 0) { $status = "PASS" }
  } finally {
    Pop-Location
  }
} catch {
  ("Runner failure (see local environment): " + $_.Exception.Message) |
    Out-File -FilePath $log -Append -Encoding utf8
  $exitCode = 2
} finally {
  $record = [ordered]@{
    status = $status
    mode = $Mode
    source_sha = $sha
    python = $pythonVersion
    exit_code = $exitCode
    started_utc = $started.ToString("o")
    completed_utc = ([DateTime]::UtcNow).ToString("o")
    local_log = $log
    real_nas_tested = $false
    registered_uliya_expert_called = $false
    release_gate = "HOLD"
  }
  $record | ConvertTo-Json -Depth 3 | Set-Content -Path $summary -Encoding UTF8
  Write-Host ("UGREEN LOCAL VERIFY: " + $status + " [" + $Mode + "]")
  Write-Host ("SHA: " + $sha)
  Write-Host ("Summary: " + $summary)
  Write-Host ("Log: " + $log)
  if ($exitCode -ne 0 -and (Test-Path -LiteralPath $log)) {
    Write-Host "Failure log (last 20 lines):"
    Get-Content -LiteralPath $log -Tail 20 | ForEach-Object { Write-Host $_ }
  }
}
exit $exitCode
