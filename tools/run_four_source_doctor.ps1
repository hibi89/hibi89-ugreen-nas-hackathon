<# Read-only UGREEN source readiness. No NAS / user content. #>
[CmdletBinding()]
param(
    [string]$HaeRoot = "..\HAE",
    [string]$SoviaRoot = "..\SOVIA_sovereign",
    [string]$DbvoraRoot = "..\DBVORA"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$script = Join-Path $repo "tools\flowpilot_source_doctor.py"
& py -3.11 $script --hae-root $HaeRoot --sovia-root $SoviaRoot --dbvora-root $DbvoraRoot
exit $LASTEXITCODE
