<#
One command: 1-, 2-, 3-intent owner-local synthetic check and JSON+HTML report.
Default no disposable SQLite writes. Never touches NAS/customer data.
#>
[CmdletBinding()]
param(
    [switch]$ApproveDisposableSynthetic,
    [string]$HaeRoot = "..\HAE",
    [string]$SoviaRoot = "..\SOVIA_sovereign",
    [string]$DbvoraRoot = "..\DBVORA",
    [string]$OutputDir = ""
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $root "tools\flowpilot_four_source_suite.py"
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
    throw "Local synthetic verification suite unavailable"
}
$arglist = @("-3.11", $script,
    "--hae-root", $HaeRoot, "--sovia-root", $SoviaRoot,
    "--dbvora-root", $DbvoraRoot)
if ($ApproveDisposableSynthetic) { $arglist += "--approve-disposable-synthetic" }
if ($OutputDir) {
    $arglist += @("--output-dir", [System.IO.Path]::GetFullPath($OutputDir))
}
& py @arglist
exit $LASTEXITCODE
