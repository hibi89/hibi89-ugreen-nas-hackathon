# G166 owner-local start only. Does not register/login/start UGREEN trial.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_g166_local.ps1 -Db C:\private\g166.sqlite -InitNewDb
param(
  [Parameter(Mandatory=$true)][string]$Db,
  [switch]$InitNewDb,
  [string]$MetadataRoot = "",
  [int]$Port = 8766,
  [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
if (-not [System.IO.Path]::IsPathRooted($Db) -or -not $Db.EndsWith(".sqlite")) {
  throw "Provide an absolute .sqlite path outside the Git repository."
}
if ($Port -lt 1024 -or $Port -gt 65535) { throw "Port must be 1024..65535." }
# Prevent even an explicitly initialized private DB from being created anywhere
# under the public checkout, not only beneath tools/ (G166 previously missed root).
$checkout = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..")).TrimEnd('\', '/')
$dbPath = [System.IO.Path]::GetFullPath($Db)
$separator = [System.IO.Path]::DirectorySeparatorChar
if ($dbPath.Equals($checkout, [System.StringComparison]::OrdinalIgnoreCase) -or
    $dbPath.StartsWith($checkout + $separator, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "DB must be outside the GitHub checkout."
}
if (-not (Test-Path -LiteralPath ([System.IO.Path]::GetDirectoryName($dbPath)) -PathType Container)) {
  throw "DB parent directory must exist; refusing implicit directory creation."
}
# G168: stored SQLite must not follow an existing NTFS junction/symlink
# to an unexpected location, including a public checkout or a network share.
# This scans the DB parent only; metadata-root remains untouched until consent.
function Assert-PlainDbParent([string]$Target) {
  $parent = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($Target))
  while (-not [string]::IsNullOrEmpty($parent)) {
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
      throw "DB parent is missing or inaccessible."
    }
    $entry = Get-Item -LiteralPath $parent -Force -ErrorAction Stop
    if (($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
      throw "DB ancestor is a symlink/junction/reparse point; refusing."
    }
    $next = [System.IO.Path]::GetDirectoryName($parent)
    if ([string]::IsNullOrEmpty($next) -or
        $next.Equals($parent, [System.StringComparison]::OrdinalIgnoreCase)) {
      break
    }
    $parent = $next
  }
  $drive = [System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($Target))
  if ($drive.StartsWith("\\\\") -or $drive.StartsWith("//")) {
    throw "Network SQLite path denied."
  }
  if ((Test-Path -LiteralPath $drive) -and
      ([System.IO.DriveInfo]::new($drive)).DriveType -eq [System.IO.DriveType]::Network) {
    throw "Mapped network SQLite volume denied."
  }
}
Assert-PlainDbParent $dbPath
if ($InitNewDb -and (Test-Path -LiteralPath $Db)) {
  throw "Database already exists; refusing -InitNewDb overwrite."
}
if (-not $InitNewDb -and -not (Test-Path -LiteralPath $Db)) {
  throw "New DB requires explicit -InitNewDb."
}
if ($MetadataRoot -ne "") {
  if (-not [System.IO.Path]::IsPathRooted($MetadataRoot)) {
    throw "MetadataRoot must be absolute and local. NAS paths are forbidden."
  }
  if ($MetadataRoot.StartsWith("\\") -or $MetadataRoot.StartsWith("//")) {
    throw "UNC/network metadata root forbidden."
  }
  # Windows drive-letter mappings can point to a remote SMB/NAS share,
  # even if a path does not start with \\. Fail closed on network drives.
  $rootPath = [System.IO.Path]::GetFullPath($MetadataRoot)
  $rootDrive = [System.IO.Path]::GetPathRoot($rootPath)
  if ($null -ne $rootDrive -and (Test-Path -LiteralPath $rootDrive)) {
    $driveType = ([System.IO.DriveInfo]::new($rootDrive)).DriveType
    if ($driveType -eq [System.IO.DriveType]::Network) {
      throw "Network/mapped NAS drive is not a permitted MetadataRoot."
    }
  }
}
$env:FLOWPILOT_LOCAL_API_TOKEN = (& $Python -c "import secrets; print(secrets.token_urlsafe(48))").Trim()
if ($LASTEXITCODE -ne 0 -or $env:FLOWPILOT_LOCAL_API_TOKEN.Length -lt 32) {
  throw "Failed to generate a sufficiently long ephemeral token."
}
$arguments = @((Join-Path $PSScriptRoot "flowpilot_local_backend.py"), "--db", $Db, "--port", "$Port")
if ($InitNewDb) { $arguments += "--init-db" }
if ($MetadataRoot -ne "") { $arguments += @("--metadata-root", $MetadataRoot) }
Write-Host ("Open browser on same machine: http://127.0.0.1:" + $Port + "/dashboard")
Write-Host "Local-only API token (paste into dashboard; do not save/share):"
Write-Host $env:FLOWPILOT_LOCAL_API_TOKEN
Write-Host "G166 local only. No NAS, no Uliya registration, no external upload. Stop with Ctrl+C."
try {
  & $Python @arguments
  exit $LASTEXITCODE
} finally {
  Remove-Item Env:FLOWPILOT_LOCAL_API_TOKEN -ErrorAction SilentlyContinue
}
