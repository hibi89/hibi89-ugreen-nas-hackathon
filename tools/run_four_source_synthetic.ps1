<#
Local-only four-source synthetic verification. No customer data or NAS calls.
Only use trusted, exact-SHA local source checkouts. Default runs preview only.
#>
[CmdletBinding()]
param(
    [switch]$ApproveDisposableSynthetic,
    [string]$HaeRoot = "..\HAE",
    [string]$SoviaRoot = "..\SOVIA_sovereign",
    [string]$DbvoraRoot = "..\DBVORA",
    [ValidateSet(1, 2, 3)][int]$IntentCount = 2
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
$script = Join-Path $repo "tools\verify_four_source_synthetic.py"
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
    throw "UGREEN four-source verifier unavailable"
}
$arglist = @("-3.11", $script,
          "--hae-root", $HaeRoot,
          "--sovia-root", $SoviaRoot,
          "--dbvora-root", $DbvoraRoot,
          "--intent-count", [string]$IntentCount)
if ($ApproveDisposableSynthetic) { $arglist += "--approve-disposable-synthetic" }
& py @args
exit $LASTEXITCODE
