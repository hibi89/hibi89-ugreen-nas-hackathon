<#
UGREEN: prepare the first-party UGOS Skill Creation Tool for owner-controlled Codex.
This copies a verified PUBLIC vendor archive into a private local Skill directory.
It does NOT execute the vendor archive, invoke an AI assistant, create a ProjectReady
Skill, perform a license audit or submit a hackathon entry.
#>
[CmdletBinding()]
param(
    [string]$PrivateRoot,
    [string]$ArchivePath,
    [switch]$InstallForCodex,
    [string]$CodexSkillsRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$officialUrl = 'https://cdn.shopify.com/s/files/1/0630/9416/1602/files/uliya-skill-kit-0.7.3-en.zip?v=1790578898'
$expectedSha256 = 'cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3'
if (-not $PrivateRoot) {
    if ($env:LOCALAPPDATA) {
        $PrivateRoot = Join-Path $env:LOCALAPPDATA 'UGREEN_OFFICIAL_SDK_PRIVATE'
    } else {
        $PrivateRoot = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.ugreen-official-sdk-private'
    }
}
if (-not $CodexSkillsRoot) {
    $CodexSkillsRoot = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.agents/skills'
}
New-Item -ItemType Directory -Force -Path $PrivateRoot | Out-Null
if (-not $ArchivePath) {
    $ArchivePath = Join-Path $PrivateRoot 'uliya-skill-kit-0.7.3-en.zip'
    if (-not (Test-Path -LiteralPath $ArchivePath)) {
        Invoke-WebRequest -Uri $officialUrl -OutFile $ArchivePath -ErrorAction Stop
    }
}
if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
    throw 'Expected first-party archive does not exist'
}
$actualSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $ArchivePath).Hash.ToLowerInvariant()
if ($actualSha -ne $expectedSha256) {
    throw "Archive SHA256 mismatch (official version may have changed). Stop and independently review the official Starter Kit. Observed: $actualSha"
}
Add-Type -AssemblyName System.IO.Compression
$fs = [System.IO.File]::OpenRead((Resolve-Path -LiteralPath $ArchivePath).ProviderPath)
try {
    $zip = [System.IO.Compression.ZipArchive]::new($fs, [System.IO.Compression.ZipArchiveMode]::Read, $false)
    try {
        $seen = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        $total = [long]0
        if ($zip.Entries.Count -gt 1000) { throw 'Too many archive members' }
        foreach ($entry in $zip.Entries) {
            $name = $entry.FullName
            if ([string]::IsNullOrWhiteSpace($name) -or $name.Contains('\') -or
                $name.StartsWith('/') -or $name.Contains(':') -or
                $name.IndexOf([char]0) -ge 0) {
                throw 'Unsafe ZIP member path'
            }
            foreach ($part in $name.TrimEnd('/').Split('/')) {
                if ($part -eq '' -or $part -eq '.' -or $part -eq '..') {
                    throw 'Unsafe ZIP traversal member'
                }
            }
            if (-not $seen.Add($name.TrimEnd('/'))) { throw 'Case-colliding ZIP member' }
            $mode = ([int]$entry.ExternalAttributes -shr 16) -band 61440
            if ($mode -eq 40960) { throw 'Symlinks not accepted from ZIP' }
            if ($entry.Length -gt 8388608) { throw 'Oversized archive member' }
            $total += $entry.Length
            if ($total -gt 67108864) { throw 'Excessive uncompressed ZIP data' }
        }
    } finally {
        $zip.Dispose()
    }
} finally {
    $fs.Dispose()
}
$stage = Join-Path $PrivateRoot ('verified-kit-' + [Guid]::NewGuid().ToString('N'))
try {
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $stage -ErrorAction Stop
    $matches = @(
        Get-ChildItem -LiteralPath $stage -Directory -Recurse | Where-Object {
            $_.Name -eq 'uliya-skill-kit' -and (Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') -PathType Leaf)
        }
    )
    if ($matches.Count -eq 1) {
        $kit = $matches[0].FullName
    } elseif ($matches.Count -eq 0 -and (Test-Path -LiteralPath (Join-Path $stage 'SKILL.md'))) {
        $kit = $stage
    } else {
        throw 'Official archive layout is ambiguous or has no root SKILL.md; no install performed'
    }
    Write-Host 'VERIFIED_PUBLIC_ARCHIVE_SHA256_MATCH'
    Write-Host 'Official kit extracted privately. No vendor script executed.'
    if ($InstallForCodex) {
        New-Item -ItemType Directory -Force -Path $CodexSkillsRoot | Out-Null
        $target = Join-Path $CodexSkillsRoot 'uliya-skill-kit'
        if (Test-Path -LiteralPath $target) {
            throw 'Existing Codex kit directory detected. Refusing to overwrite; inspect and back up first.'
        }
        Copy-Item -LiteralPath $kit -Destination $target -Recurse -ErrorAction Stop
        if (-not (Test-Path -LiteralPath (Join-Path $target 'SKILL.md') -PathType Leaf)) {
            throw 'Copied Codex kit lacks SKILL.md'
        }
        Write-Host 'CODEX_SKILL_FOLDER_COPIED_ONLY'
        Write-Host "Kit location: $target"
        Write-Host 'Restart Codex; explicitly verify official kit discovery and CREATE a new Skill.'
    } else {
        Write-Host 'DRY_PREP_ONLY: no Codex skills installation. Add -InstallForCodex when ready.'
    }
    Write-Host 'OFFICIAL_CREATION_NOT_RUN; OFFICIAL_CHECKER_NOT_RUN; NO_NAS; NO_DEVPOST.'
} finally {
    # The actual installed copy (if requested) is separate; only ephemeral stage is removed.
    if (Test-Path -LiteralPath $stage) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
