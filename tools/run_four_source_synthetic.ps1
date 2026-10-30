<#
Local-only four-source synthetic verification. No customer data or NAS calls.
Only use trusted, exact-SHA local source checkouts. Default runs preview only.
#>
[CmdletBinding()]
param(
    [switch]$ApproveDisposableSynthetic,
    [string]$HaeRoot = "..\HAE",
    [string]$SoviaRoot = "..\SOVIA_sovereign",
    [string]$DbvoraRoot = "..\DBVORA"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$script = Join-Path $repo "tools\verify_four_source_synthetic.py"
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
    throw "UGREEN four-source verifier unavailable"
}
$args = @("-3.11", $script,
          "--hae-root", $HaeRoot,
          "--sovia-root", $SoviaRoot,
          "--dbvora-root", $DbvoraRoot)
if ($ApproveDisposableSynthetic) { $args += "--approve-disposable-synthetic" }
& py @args
exit $LASTEXITCODE
