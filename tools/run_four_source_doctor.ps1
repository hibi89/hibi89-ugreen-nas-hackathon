<# Read-only UGREEN source readiness. No NAS / user content. #>
[CmdletBinding()]
param(
    [string]$HaeRoot = "..\HAE",
    [string]$SoviaRoot = "..\SOVIA_sovereign",
    [string]$DbvoraRoot = "..\DBVORA"
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
$script = Join-Path $repo "tools\flowpilot_source_doctor.py"
& py -3.11 $script --hae-root $HaeRoot --sovia-root $SoviaRoot --dbvora-root $DbvoraRoot
exit $LASTEXITCODE
