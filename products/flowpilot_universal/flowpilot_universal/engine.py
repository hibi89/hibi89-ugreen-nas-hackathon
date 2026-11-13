"""Offline-only, fail-closed verification for an explicitly authorized delivery folder."""
from __future__ import annotations
import hashlib
import html
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Callable

MANIFEST_LIMIT = 1_048_576
MAX_FILES = 20_000
MAX_BYTES = 8 * 1024**3
CHUNK_SIZE = 1024 * 1024
VERSION_RE = re.compile(r"(?i)(?:[ ._-]*(?:ver(?:sion)?|rev|v|r)[ ._-]*\d+|[ ._-]*(?:final|copy|복사본)(?:[ ._-]*\d+)?)$")

class InputError(ValueError):
    """Untrusted manifest, root, or output path refused."""

def _positive_integer(value: Any, field: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise InputError(f"{field} must be an integer in 1..{maximum}")
    return value

def _relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise InputError("requirement paths must be nonempty relative POSIX paths")
    parts = value.split("/")
    if (value.startswith("/") or any(p in ("", ".", "..") for p in parts)
            or any(":" in p or p.rstrip(" .") != p for p in parts)):
        raise InputError("unsafe requirement path")
    return value

def load_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise InputError("manifest must be a regular local file")
    if path.stat().st_size > MANIFEST_LIMIT:
        raise InputError("manifest exceeds size limit")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("invalid UTF-8 manifest JSON") from exc
    if not isinstance(raw, dict) or set(raw) - {"schema_version", "expected_files", "limits", "title"}:
        raise InputError("manifest contains unknown fields or is not an object")
    if raw.get("schema_version") != 1 or isinstance(raw.get("schema_version"), bool):
        raise InputError("schema_version must be 1")
    title = raw.get("title", "FlowPilot delivery verification")
    if not isinstance(title, str) or len(title) > 160:
        raise InputError("title must be a string of at most 160 chars")
    files = raw.get("expected_files")
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise InputError("expected_files must contain 1..20000 entries")
    seen: set[str] = set()
    normalized = []
    for item in files:
        if not isinstance(item, dict) or set(item) - {"path", "sha256"}:
            raise InputError("unexpected expected_files entry")
        rel = _relative(item.get("path"))
        folded = rel.casefold()
        if folded in seen:
            raise InputError("duplicate or case-colliding required path")
        seen.add(folded)
        digest = item.get("sha256")
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest)):
            raise InputError("sha256 must be a 64-digit hexadecimal string")
        normalized.append({"path": rel, "sha256": digest.lower() if digest else None})
    limits = raw.get("limits", {})
    if not isinstance(limits, dict) or set(limits) - {"max_files", "max_bytes"}:
        raise InputError("unknown scan limits")
    return {"title": title, "schema_version": 1, "expected_files": normalized,
            "limits": {"max_files": _positive_integer(limits.get("max_files", MAX_FILES), "max_files", MAX_FILES),
                       "max_bytes": _positive_integer(limits.get("max_bytes", MAX_BYTES), "max_bytes", MAX_BYTES)}}

def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))

def _signature(info: os.stat_result) -> tuple[int, int, int, int]:
    # CPython on Windows may report differing path/FD volume or file IDs.
    # Compare size and mtime there; full identity/race hardening remains a P70 gate.
    if os.name == "nt":
        return (0, 0, info.st_size, info.st_mtime_ns)
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)

def _hash_file(path: Path, before: os.stat_result, cancel: Callable[[], bool] | None = None) -> str:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    handle = os.open(path, flags)
    try:
        opened = os.fstat(handle)
        if not stat.S_ISREG(opened.st_mode) or _signature(opened) != _signature(before):
            raise OSError("file changed between stat and open")
        digest = hashlib.sha256()
        with os.fdopen(os.dup(handle), "rb", closefd=True) as stream:
            while data := stream.read(CHUNK_SIZE):
                if cancel is not None and cancel():
                    raise InterruptedError("scan cancelled during hash")
                digest.update(data)
        if (_signature(os.fstat(handle)) != _signature(before)
                or _signature(path.lstat()) != _signature(before)):
            raise OSError("file changed during hashing")
        return digest.hexdigest()
    finally:
        os.close(handle)

def _version_key(rel: str) -> str | None:
    parent, _, base = rel.rpartition("/")
    stem, dot, suffix = base.rpartition(".")
    if not dot:
        stem, suffix = base, ""
    reduced = stem
    while True:
        changed = VERSION_RE.sub("", reduced)
        if changed == reduced:
            break
        reduced = changed
    if reduced and reduced != stem:
        return f"{parent.casefold()}/{reduced.casefold()}.{suffix.casefold()}"
    return None

def scan(root: Path, manifest: dict[str, Any], *,
         cancel: Callable[[], bool] | None = None,
         progress: Callable[[int, int], None] | None = None) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise InputError("root must be an existing non-symlink directory explicitly approved by the operator")
    root = root.resolve(strict=True)
    files: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    byte_count = 0
    traversed = 0
    stack: list[tuple[Path, str]] = [(root, "")]
    stopped = False
    max_files = manifest["limits"]["max_files"]
    max_bytes = manifest["limits"]["max_bytes"]
    while stack and not stopped:
        if cancel is not None and cancel():
            issues.append({"code": "SCAN_INTERRUPTED", "path": "."})
            stopped = True
            break
        directory, prefix = stack.pop()
        try:
            dir_before = directory.lstat()
            if _is_link(dir_before) or not stat.S_ISDIR(dir_before.st_mode):
                issues.append({"code": "DIRECTORY_UNSAFE", "path": prefix or "."})
                continue
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda e: (e.name.casefold(), e.name))
        except OSError:
            issues.append({"code": "DIRECTORY_UNREADABLE", "path": prefix or "."})
            continue
        for entry in entries:
            if cancel is not None and cancel():
                issues.append({"code": "SCAN_INTERRUPTED", "path": prefix or "."})
                stopped = True
                break
            rel = prefix + entry.name
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                issues.append({"code": "ENTRY_UNREADABLE", "path": rel})
                continue
            if _is_link(info):
                issues.append({"code": "UNSAFE_LINK", "path": rel})
            elif stat.S_ISDIR(info.st_mode):
                stack.append((Path(entry.path), rel + "/"))
            elif stat.S_ISREG(info.st_mode):
                traversed += 1
                byte_count += info.st_size
                if traversed > max_files or byte_count > max_bytes:
                    issues.append({"code": "SCAN_LIMIT", "path": rel})
                    stopped = True
                    break
                record: dict[str, Any] = {"path": rel, "size": info.st_size, "sha256": None}
                try:
                    record["sha256"] = _hash_file(Path(entry.path), info, cancel)
                except OSError:
                    issues.append({"code": "FILE_UNREADABLE_OR_CHANGED", "path": rel})
                files.append(record)
                if progress is not None:
                    progress(len(files), byte_count)
            else:
                issues.append({"code": "UNSUPPORTED_FILE_TYPE", "path": rel})
        try:
            dir_after = directory.lstat()
            # Directory mtimes are not reliable on Windows/SMB. Relist names as
            # an additional fail-closed check; this is not an atomic snapshot.
            with os.scandir(directory) as verify_iterator:
                after_names = sorted(item.name for item in verify_iterator)
            before_names = sorted(item.name for item in entries)
            if (_is_link(dir_after) or not stat.S_ISDIR(dir_after.st_mode)
                    or dir_before.st_mtime_ns != dir_after.st_mtime_ns
                    or before_names != after_names
                    or (os.name != "nt" and (dir_before.st_dev, dir_before.st_ino) !=
                        (dir_after.st_dev, dir_after.st_ino))):
                issues.append({"code": "DIRECTORY_CHANGED", "path": prefix or "."})
        except OSError:
            issues.append({"code": "DIRECTORY_CHANGED", "path": prefix or "."})
    files.sort(key=lambda rec: (rec["path"].casefold(), rec["path"]))
    indexed: dict[str, dict[str, Any]] = {}
    for rec in files:
        folded = rec["path"].casefold()
        if folded in indexed:
            issues.append({"code": "CASE_COLLISION", "paths": [indexed[folded]["path"], rec["path"]]})
        indexed[folded] = rec
    for requirement in manifest["expected_files"]:
        actual = indexed.get(requirement["path"].casefold())
        if actual is None:
            issues.append({"code": "MISSING_REQUIRED", "path": requirement["path"]})
        elif requirement["sha256"] and actual["sha256"] and actual["sha256"] != requirement["sha256"]:
            issues.append({"code": "HASH_MISMATCH", "path": requirement["path"]})
    duplicates: dict[tuple[str, int], list[str]] = {}
    for rec in files:
        if rec["sha256"]:
            duplicates.setdefault((rec["sha256"], rec["size"]), []).append(rec["path"])
    for paths in duplicates.values():
        if len(paths) > 1:
            issues.append({"code": "DUPLICATE_CONTENT_REVIEW", "paths": sorted(paths)})
    versions: dict[str, list[str]] = {}
    for rec in files:
        key = _version_key(rec["path"])
        if key:
            versions.setdefault(key, []).append(rec["path"])
    for paths in versions.values():
        if len(paths) > 1:
            issues.append({"code": "VERSION_CANDIDATES_REVIEW", "paths": sorted(paths)})
    codes = {issue["code"] for issue in issues}
    incomplete_codes = {"DIRECTORY_UNREADABLE", "DIRECTORY_UNSAFE", "DIRECTORY_CHANGED",
                        "ENTRY_UNREADABLE", "UNSAFE_LINK", "SCAN_LIMIT", "SCAN_INTERRUPTED",
                        "FILE_UNREADABLE_OR_CHANGED", "UNSUPPORTED_FILE_TYPE", "CASE_COLLISION"}
    status = ("INCOMPLETE" if codes & incomplete_codes else
              "BLOCKED" if codes & {"MISSING_REQUIRED", "HASH_MISMATCH"} else
              "NEEDS_REVIEW" if issues else "READY")
    return {"schema_version": 1, "title": manifest["title"], "status": status,
            "root": str(root), "expected_count": len(manifest["expected_files"]),
            "files_scanned": len(files), "bytes_seen": byte_count, "files": files, "issues": issues,
            "safety": {"read_only": True, "network_used": False, "nas_actions": False,
                       "ready_requires_complete_scan": True}}

def render_html(report: dict[str, Any]) -> str:
    esc = lambda obj: html.escape(str(obj), quote=True)
    rows = "".join(f"<tr><td>{esc(x['path'])}</td><td>{x['size']}</td><td><code>{esc(x['sha256'] or 'NOT_READ')}</code></td></tr>" for x in report["files"])
    issues = "".join(f"<li>{esc(x['code'])}: {esc(x.get('path', ', '.join(x.get('paths', []))))}</li>" for x in report["issues"])
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'\">"
            f"<title>{esc(report['title'])}</title><style>body{{font:16px system-ui;max-width:1100px;margin:3rem auto;padding:1rem}}"
            "table{border-collapse:collapse;width:100%;overflow-wrap:anywhere}td,th{border:1px solid #888;padding:.5rem}"
            "code{font-size:.75rem}</style></head><body>"
            f"<h1>{esc(report['title'])}</h1><p>Result: <strong>{esc(report['status'])}</strong></p>"
            "<p>Offline read-only evidence; no NAS action, file mutation, or release approval.</p>"
            f"<p>Root: {esc(report['root'])}; files: {report['files_scanned']}; required: {report['expected_count']}</p>"
            f"<h2>Issues</h2><ul>{issues}</ul><h2>Scanned files</h2><table><thead><tr><th>Path</th>"
            f"<th>Bytes</th><th>SHA-256</th></tr></thead><tbody>{rows}</tbody></table></body></html>")

def create_only(path: Path, content: str, root: Path) -> None:
    target = path.absolute()
    parent = target.parent.resolve(strict=True)
    canonical_root = root.resolve(strict=True)
    if parent == canonical_root or canonical_root in parent.parents:
        raise InputError("refusing to write evidence inside inspected root")
    if not parent.is_dir() or path.exists() or path.is_symlink():
        raise InputError("output must be a new path in an existing directory")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(content.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        # Fail closed: keep the partial output for review, never delete automatically.
        raise
