# UGREEN G1 — personal, private official toolkit inspection (Windows)
# Run locally in Windows PowerShell ONLY after confirming the official URL
# https://ai.ugreen.com/pages/hackathon-starter-kit
# Does NOT execute SDK scripts, install tools, access NAS, or upload data.
# Official ZIP is stored under your private LOCALAPPDATA, not GitHub.

$ErrorActionPreference = 'Stop'
$official = 'https://cdn.shopify.com/s/files/1/0630/9416/1602/files/uliya-skill-kit-0.7.3-en.zip?v=1790578898'
$expected = 'cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3'
$root = Join-Path $env:LOCALAPPDATA 'UGREEN_OFFICIAL_SDK_PRIVATE'
$archive = Join-Path $root 'uliya-skill-kit-0.7.3-en.zip'
$folder = Join-Path $root 'inspection'
New-Item -ItemType Directory -Force -Path $root | Out-Null
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri $official -OutFile $archive -ErrorAction Stop
}
$got = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
if ($got -ne $expected) {
    Write-Error "Official ZIP changed or differs from checked version. Expected $expected, got $got. Do NOT extract before checking the new official version."
    exit 2
}
if (Test-Path -LiteralPath $folder) {
    Write-Error "Inspection folder already exists; will not overwrite: $folder"
    exit 3
}
# Verified hash matches the 2026-10-24 official archive inspected on
# GitHub Actions run 40064613266 (26 files, no archive traversal).
Expand-Archive -LiteralPath $archive -DestinationPath $folder -ErrorAction Stop
Write-Host "Official ZIP hash matched; extracted in a PRIVATE local folder."
Write-Host "Private SDK path: $folder"
Write-Host "Open the official SKILL.md/instructions with a supported assistant (Codex/Claude/WorkBuddy)."
Write-Host "Ask which Expert Agents are registered and which exact supported UGOS CLI commands are available."
Write-Host "Do NOT run unknown scripts, submit proprietary SDK archive, or paste secrets into Public GitHub."
