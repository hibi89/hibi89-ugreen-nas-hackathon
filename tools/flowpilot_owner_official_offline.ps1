# G152 owner-local Windows PowerShell 5.1 path; no clone, download, or upload.
# Requires a pre-existing trusted checkout and owner-private G147 files.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ArtifactFolder,
    [Parameter(Mandatory=$true)][string]$OfficialKitZip,
    [switch]$ExecuteOfficialNativeCode,
    [switch]$RequirePdfText,
    [switch]$PreflightOnly
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Refuse([string]$Reason) {
    $report = [ordered]@{
        schema = 'flowpilot-g152-offline-windows-launcher-v1'
        status = 'OWNER_LOCAL_LAUNCH_REFUSED'
        reason = $Reason
        official_checker_executed = $false
        private_artifacts_uploaded = $false
        release_gate = 'HOLD'
    }
    Write-Output ($report | ConvertTo-Json -Compress)
    exit 2
}

$entry = Join-Path $PSScriptRoot 'flowpilot_owner_official_oneshot.py'
$checker = Join-Path $PSScriptRoot 'flowpilot3_official_checker.py'
$gate = Join-Path $PSScriptRoot 'flowpilot_artifact_manifest_gate.py'
if (!(Test-Path -LiteralPath $entry -PathType Leaf) -or
    !(Test-Path -LiteralPath $checker -PathType Leaf) -or
    !(Test-Path -LiteralPath $gate -PathType Leaf)) {
    Refuse 'LOCAL_CHECKOUT_MODULES_MISSING'
}
$python = Get-Command 'python' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $python) { Refuse 'PYTHON_311_OR_NEWER_REQUIRED' }
& $python.Source -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 2)'
if ($LASTEXITCODE -ne 0) { Refuse 'PYTHON_311_OR_NEWER_REQUIRED' }

if ($PreflightOnly) {
    if ($ExecuteOfficialNativeCode) { Refuse 'EXECUTION_NOT_ALLOWED_DURING_PREFLIGHT' }
    Write-Output '{"schema":"flowpilot-g152-offline-windows-launcher-v1","status":"LOCAL_CHECKOUT_PYTHON_READY_NO_OWNER_INPUT_READ","official_checker_executed":false,"private_artifacts_uploaded":false,"release_gate":"HOLD"}'
    exit 0
}

if (!(Test-Path -LiteralPath $ArtifactFolder -PathType Container)) {
    Refuse 'OWNER_ARTIFACT_FOLDER_MISSING'
}
if (!(Test-Path -LiteralPath $OfficialKitZip -PathType Leaf)) {
    Refuse 'LOCAL_VENDOR_KIT_FILE_MISSING'
}

if ($ExecuteOfficialNativeCode) {
    # Only an explicit switch permits official vendor JS execution.
    # This preflight must not be treated as proof of the vendor Checker result.
    $node = Get-Command 'node' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $node) { Refuse 'NODE_22_OR_NEWER_REQUIRED' }
    $nodeVersion = & $node.Source --version
    if ($LASTEXITCODE -ne 0 -or $nodeVersion -notmatch '^v([0-9]+)\.') {
        Refuse 'NODE_22_OR_NEWER_REQUIRED'
    }
    if ([int]$Matches[1] -lt 22) { Refuse 'NODE_22_OR_NEWER_REQUIRED' }
}

$runnerArgs = @($entry, '--folder', $ArtifactFolder, '--official-kit-zip', $OfficialKitZip)
if ($RequirePdfText) { $runnerArgs += '--require-pdf-text' }
if ($ExecuteOfficialNativeCode) { $runnerArgs += '--execute-official-native-code' }
& $python.Source @runnerArgs
exit $LASTEXITCODE
