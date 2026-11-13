# Windows-only, local, unsigned ZIP installation rehearsal.
# CI synthetic evidence only: do not distribute or run on a customer's system.
# No registry edits, services, privileges, global PATH, shortcuts or external traffic.
# Only accepts a NEW directory directly beneath the CI runner temporary directory.
param(
  [Parameter(Mandatory=$true)][ValidateSet('Install','Verify','Remove')][string]$Mode,
  [Parameter(Mandatory=$true)][string]$WorkDir,
  [string]$ZipPath = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Stop-Hold([string]$message) { throw "HOLD: $message" }
function Get-SHA([string]$file) { return (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() }
function Assert-WorkDir {
  if (-not $env:RUNNER_TEMP) { Stop-Hold 'CI RUNNER_TEMP required; never run against consumer files' }
  $allowed = [IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
  $target = [IO.Path]::GetFullPath($WorkDir).TrimEnd('\')
  if (-not [string]::Equals([IO.Path]::GetDirectoryName($target), $allowed,
                            [StringComparison]::OrdinalIgnoreCase)) {
    Stop-Hold 'WorkDir must be a direct child of CI runner temporary folder'
  }
  return $target
}
function Read-Manifest([string]$folder) {
  $marker = Join-Path $folder 'FLOWPILOT_CANDIDATE_SHA256.json'
  if (-not [IO.File]::Exists($marker)) { Stop-Hold 'candidate index missing' }
  $obj = Get-Content -LiteralPath $marker -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($obj.format -ne 'flowpilot-unsigned-onedir-v1' -or $obj.signed -ne $false -or
      $obj.release_approved -ne $false) { Stop-Hold 'wrong or signed/released claim in index' }
  return $obj
}
function Expected-Names([object]$obj) {
  $names = @($obj.files.PSObject.Properties.Name)
  if ($names.Count -lt 1 -or $names.Count -gt 5000 -or
      $names -notcontains 'FlowPilotUniversal/FlowPilotUniversal.exe') {
    Stop-Hold 'candidate package index lacks main executable'
  }
  $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach ($name in $names) {
    $parts = $name.Split('/')
    if ($parts.Count -lt 2 -or $parts[0] -cne 'FlowPilotUniversal' -or
        ($parts | Where-Object { $_ -in @('', '.', '..') -or $_ -match '[\\:<>"|?*\x00-\x1f]' }).Count -gt 0 -or
        -not $seen.Add($name)) { Stop-Hold 'duplicate or unsafe archive member' }
  }
  return $names
}
function Verify-Files([string]$folder, [object]$obj) {
  $names = @(Expected-Names $obj)
  $expected = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  [void]$expected.Add('FLOWPILOT_CANDIDATE_SHA256.json')
  foreach ($name in $names) { [void]$expected.Add($name.Replace('/','\')) }
  $dirs = @(Get-ChildItem -LiteralPath $folder -Recurse -Force -Directory)
  if (@($dirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -ne 0) {
    Stop-Hold 'installed folder contains a directory reparse point; preserve files'
  }
  $all = @(Get-ChildItem -LiteralPath $folder -Recurse -Force -File)
  if ($all.Count -ne $expected.Count) { Stop-Hold 'unknown or missing installed file; preserve customer data' }
  foreach ($item in $all) {
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
      Stop-Hold 'candidate folder contains reparse files'
    }
    $relative = [IO.Path]::GetRelativePath($folder, $item.FullName)
    if (-not $expected.Contains($relative)) { Stop-Hold 'unknown file; preserve existing data' }
  }
  foreach ($name in $names) {
    $file = Join-Path $folder ($name.Replace('/','\'))
    $record = $obj.files.PSObject.Properties[$name].Value
    if (-not [IO.File]::Exists($file) -or
        (Get-Item -LiteralPath $file).Length -ne [long]$record.size -or
        (Get-SHA $file) -cne [string]$record.sha256) {
      Stop-Hold 'candidate member SHA mismatch; refuse further work'
    }
  }
}
$root = Assert-WorkDir
switch ($Mode) {
  'Install' {
    if ([IO.Directory]::Exists($root) -or [IO.File]::Exists($root)) {
      Stop-Hold 'never overwrite existing destination'
    }
    if (-not $ZipPath -or -not [IO.File]::Exists([IO.Path]::GetFullPath($ZipPath))) {
      Stop-Hold 'candidate ZIP unavailable'
    }
    $archive = [IO.Compression.ZipFile]::OpenRead([IO.Path]::GetFullPath($ZipPath))
    try {
      $indexEntries = @($archive.Entries | Where-Object { $_.FullName -ceq 'FLOWPILOT_CANDIDATE_SHA256.json' })
      if ($indexEntries.Count -ne 1 -or $indexEntries[0].Length -gt 2000000) {
        Stop-Hold 'index not unique or too large'
      }
      $reader = [IO.StreamReader]::new($indexEntries[0].Open(), [Text.Encoding]::UTF8)
      try { $obj = ($reader.ReadToEnd() | ConvertFrom-Json) } finally { $reader.Dispose() }
      if ($obj.format -ne 'flowpilot-unsigned-onedir-v1' -or
          $obj.signed -ne $false -or $obj.release_approved -ne $false) {
        Stop-Hold 'unapproved source archive'
      }
      $names = @(Expected-Names $obj)
      $zipNames = @($archive.Entries | ForEach-Object { $_.FullName })
      $expected = @($names) + @('FLOWPILOT_CANDIDATE_SHA256.json')
      if ($zipNames.Count -ne $expected.Count) { Stop-Hold 'unexpected zip members' }
      foreach ($entry in $archive.Entries) {
        if ($expected -cnotcontains $entry.FullName -or $entry.Length -gt 180MB) {
          Stop-Hold 'unrecognized or oversized ZIP member'
        }
      }
      [void][IO.Directory]::CreateDirectory($root)
      foreach ($entry in $archive.Entries) {
        $destination = Join-Path $root ($entry.FullName.Replace('/','\'))
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
        $source = $entry.Open()
        $target = [IO.File]::Open($destination, [IO.FileMode]::CreateNew,
                                  [IO.FileAccess]::Write, [IO.FileShare]::None)
        try { $source.CopyTo($target) } finally { $source.Dispose(); $target.Dispose() }
      }
      Verify-Files $root $obj
      Write-Host 'INSTALL_CANDIDATE_VERIFIED'
    } finally { $archive.Dispose() }
  }
  'Verify' {
    if (-not [IO.Directory]::Exists($root)) { Stop-Hold 'not installed' }
    Verify-Files $root (Read-Manifest $root)
    Write-Host 'INSTALLED_FILES_VERIFIED'
  }
  'Remove' {
    if (-not [IO.Directory]::Exists($root)) { Stop-Hold 'not installed' }
    $obj = Read-Manifest $root
    Verify-Files $root $obj
    # Refuse unknown files before deleting; never delete modified or added data.
    foreach ($name in @(Expected-Names $obj)) {
      [IO.File]::Delete((Join-Path $root ($name.Replace('/','\'))))
    }
    [IO.File]::Delete((Join-Path $root 'FLOWPILOT_CANDIDATE_SHA256.json'))
    $folders = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force |
                 Sort-Object { $_.FullName.Length } -Descending)
    foreach ($dir in $folders) { [IO.Directory]::Delete($dir.FullName, $false) }
    [IO.Directory]::Delete($root, $false)
    Write-Host 'CANDIDATE_REMOVED_NO_OTHER_FILES'
  }
}
