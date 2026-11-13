"""Local-only unsigned Windows EXE folder packaging and integrity rehearsal.

This package is a CI CANDIDATE, not a commercial release or trusted signature.
No upload, network, certificate, registry or installer operations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import zipfile

FILE_CAP = 5000
BYTE_CAP = 600 * 1024**2
SINGLE_CAP = 180 * 1024**2
INDEX_NAME = "FLOWPILOT_CANDIDATE_SHA256.json"
ARCHIVE_FOLDER = "FlowPilotUniversal"
ZIP_CAP = 650 * 1024**2


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel(name: str) -> str:
    if (not isinstance(name, str) or name.startswith("/") or "\\" in name
            or any(part in ("", ".", "..") for part in name.split("/"))
            or "\x00" in name):
        raise ValueError("unsafe package member path")
    return name


def build_candidate(source: Path, target: Path) -> str:
    """Create-only ZIP and verified deterministic member index from local onedir."""
    if source.is_symlink() or not source.is_dir() or source.name != ARCHIVE_FOLDER:
        raise ValueError("source must be the real FlowPilotUniversal onedir folder")
    if os.path.lexists(target) or target.suffix.lower() != ".zip":
        raise ValueError("candidate ZIP must have a new .zip filename")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise ValueError("ZIP parent must be an existing directory")
    folder = source.resolve(strict=True)
    output_parent = target.parent.resolve(strict=True)
    if output_parent == folder or folder in output_parent.parents:
        raise ValueError("candidate ZIP cannot be stored inside source")
    members: dict[str, dict[str, int | str]] = {}
    byte_count = 0
    entries: list[tuple[Path, str]] = []
    for item in sorted(source.rglob("*")):
        info = item.lstat()
        if stat.S_ISDIR(info.st_mode):
            if item.is_symlink():
                raise ValueError("symlink directory refused")
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or item.is_symlink():
            raise ValueError("refuse linked or non-file archive member")
        if info.st_size > SINGLE_CAP:
            raise ValueError("file exceeds size cap")
        name = _rel(f"{ARCHIVE_FOLDER}/{item.relative_to(source).as_posix()}")
        byte_count += info.st_size
        if len(entries) >= FILE_CAP or byte_count > BYTE_CAP:
            raise ValueError("candidate folder too large")
        entries.append((item, name))
    if not any(name.endswith("/FlowPilotUniversal.exe") for _, name in entries):
        raise ValueError("candidate is missing EXE")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED,
                                 allowZip64=False) as archive:
                for path, name in entries:
                    before = path.lstat()
                    with path.open("rb") as src:
                        content = src.read(SINGLE_CAP + 1)
                    if len(content) != before.st_size or path.lstat().st_mtime_ns != before.st_mtime_ns:
                        raise ValueError("candidate source changed while archiving")
                    members[name] = {"sha256": _sha(content), "size": len(content)}
                    archive.writestr(name, content)
                index = {
                    "format": "flowpilot-unsigned-onedir-v1",
                    "signed": False, "release_approved": False,
                    "files": members,
                }
                archive.writestr(INDEX_NAME,
                                json.dumps(index, sort_keys=True, separators=(",", ":")).encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        return verify_candidate(target)
    except BaseException:
        # Never silently delete incomplete candidate; manual inspection is required.
        raise


def verify_candidate(path: Path) -> str:
    """Non-executing integrity check. No extraction of untrusted paths."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > ZIP_CAP:
        raise ValueError("invalid or oversized candidate ZIP")
    with zipfile.ZipFile(path, "r") as archive:
        files = archive.infolist()
        names = [x.filename for x in files]
        if len(files) > FILE_CAP + 1 or len(names) != len(set(names)) or INDEX_NAME not in names:
            raise ValueError("duplicate/missing/oversized package entries")
        if sum(x.file_size for x in files) > BYTE_CAP + 2_000_000:
            raise ValueError("uncompressed zip exceeds byte cap")
        index_info = archive.getinfo(INDEX_NAME)
        if index_info.file_size > 2_000_000:
            raise ValueError("package manifest too large")
        index = json.loads(archive.read(INDEX_NAME))
        if (index.get("format") != "flowpilot-unsigned-onedir-v1"
                or index.get("signed") is not False
                or index.get("release_approved") is not False):
            raise ValueError("unsupported package index")
        contents = index.get("files")
        if not isinstance(contents, dict) or set(contents) != (set(names) - {INDEX_NAME}):
            raise ValueError("package files do not match recorded index")
        if not any(n == f"{ARCHIVE_FOLDER}/FlowPilotUniversal.exe" for n in contents):
            raise ValueError("candidate lacks executable")
        for info in files:
            name = _rel(info.filename)
            if info.is_dir() or info.file_size > SINGLE_CAP or info.compress_size > SINGLE_CAP:
                raise ValueError("untrusted zip member")
            if name == INDEX_NAME:
                continue
            if not name.startswith(ARCHIVE_FOLDER + "/"):
                raise ValueError("archive member outside executable folder")
            rec = contents[name]
            if (not isinstance(rec, dict) or not isinstance(rec.get("size"), int)
                    or rec["size"] != info.file_size or
                    not isinstance(rec.get("sha256"), str) or
                    re.fullmatch(r"[0-9a-f]{64}", rec["sha256"]) is None):
                raise ValueError("invalid SHA metadata")
            if _sha(archive.read(name)) != rec["sha256"]:
                raise ValueError("tampered candidate")
    return _sha(path.read_bytes())


def extract_verified(path: Path, output: Path) -> Path:
    """Verified local candidate only, new directory, never replace contents."""
    verify_candidate(path)
    if os.path.lexists(output):
        raise ValueError("extraction requires a new, nonexistent folder")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError("extraction parent must exist")
    output.mkdir(mode=0o700)
    with zipfile.ZipFile(path, "r") as archive:
        archive.extractall(output)
    return output / ARCHIVE_FOLDER


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--build", nargs=2, metavar=("FOLDER", "NEW_ZIP"))
    actions.add_argument("--verify", metavar="ZIP")
    actions.add_argument("--extract", nargs=2, metavar=("ZIP", "NEW_FOLDER"))
    args = parser.parse_args(argv)
    try:
        if args.build:
            print("UNSIGNED_CANDIDATE_SHA256", build_candidate(Path(args.build[0]), Path(args.build[1])))
        elif args.verify:
            print("VERIFIED_CANDIDATE_SHA256", verify_candidate(Path(args.verify)))
        else:
            print("RELOCATED", extract_verified(Path(args.extract[0]), Path(args.extract[1])))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print("HOLD:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
