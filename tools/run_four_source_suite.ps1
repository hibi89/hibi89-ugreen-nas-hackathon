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
$repo = Split-Path -Parent $PSScriptRoot
function Resolve-SourceRoot([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "Empty source root" }
    if ([System.IO.Path]::IsPathRooted($Value)) {
        return [System.IO.Path]::GetFullPath($Value)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $repo $Value))
}
$HaeRoot = Resolve-SourceRoot $HaeRoot
$SoviaRoot = Resolve-SourceRoot $SoviaRoot
$DbvoraRoot = Resolve-SourceRoot $DbvoraRoot
$script = Join-Path $repo "tools\flowpilot_four_source_suite.py"
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
    throw "Local synthetic verification suite unavailable"
}
$arglist = @("-3.11", $script,
    "--hae-root", $HaeRoot, "--sovia-root", $SoviaRoot,
    "--dbvora-root", $DbvoraRoot)
if ($ApproveDisposableSynthetic) { $arglist += "--approve-disposable-synthetic" }
if ($OutputDir) {
    $resolved = if ([System.IO.Path]::IsPathRooted($OutputDir)) {
        [System.IO.Path]::GetFullPath($OutputDir)
    } else {
        [System.IO.Path]::GetFullPath((Join-Path $repo $OutputDir))
    }
    $arglist += @("--output-dir", $resolved)
}
& py @arglist
exit $LASTEXITCODE
