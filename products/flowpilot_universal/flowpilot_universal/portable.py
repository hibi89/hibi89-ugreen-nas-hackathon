"""Deterministic, offline, create-only Python zipapp packaging and verification.

This is a .pyz requiring a local Python 3.11+ runtime, NOT a signed Windows EXE.
The application code never contacts remote services. Archive code is not
executed by the verifier; only bounded ZIP entries and SHA-256 are inspected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import zipfile

from .engine import InputError

MODULES = ("__init__.py", "__main__.py", "engine.py", "session.py", "gui.py", "portable.py")
PACKAGE = "flowpilot_universal"
MANIFEST = "FLOWPILOT_SOURCE_MANIFEST.json"
ROOT_MAIN = "__main__.py"
MAX_ARCHIVE = 2_000_000
MAX_MEMBER = 350_000
ENTRY = (
    "import sys\n"
    "if '--gui' in sys.argv[1:]:\n"
    "    if sys.argv[1:] != ['--gui']:\n"
    "        raise SystemExit('GUI mode accepts no other options')\n"
    "    from flowpilot_universal.gui import main\n"
    "    main()\n"
    "else:\n"
    "    from flowpilot_universal.__main__ import main\n"
    "    raise SystemExit(main())\n"
)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expected() -> set[str]:
    return {ROOT_MAIN, MANIFEST} | {f"{PACKAGE}/{m}" for m in MODULES}


def _info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info


def _guard_output(path: Path, source: Path) -> Path:
    if path.is_symlink() or os.path.lexists(path):
        raise InputError("refuse overwrite or symlink for portable output")
    target = path.absolute()
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise InputError("portable output parent must be an existing real folder")
    resolved_parent = target.parent.resolve(strict=True)
    src = source.resolve(strict=True)
    if resolved_parent == src or src in resolved_parent.parents:
        raise InputError("portable artifact must be outside source tree")
    return target


def build_archive(source: Path, target: Path) -> tuple[Path, str]:
    """Build deterministic source-bound archive and create-only SHA sidecar.

    Source is local and must contain only known first-party Python modules.
    Non-regular links and files that change during source reads fail closed.
    """
    if source.is_symlink() or not source.is_dir():
        raise InputError("invalid product source directory")
    output = _guard_output(target, source)
    sidecar = output.with_name(output.name + ".sha256")
    _guard_output(sidecar, source)
    files: dict[str, bytes] = {ROOT_MAIN: ENTRY.encode("utf-8")}
    for name in MODULES:
        path = source / PACKAGE / name
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise InputError("unsafe or hardlinked package source")
        if info.st_size > MAX_MEMBER:
            raise InputError("source module too large")
        data = path.read_bytes()
        if len(data) != info.st_size or path.lstat().st_mtime_ns != info.st_mtime_ns:
            raise InputError("source changed during package build")
        files[f"{PACKAGE}/{name}"] = data
    index = {
        "format": "flowpilot-universal-pyz-v1",
        "min_python": "3.11",
        "entries": {name: _digest(data) for name, data in sorted(files.items())},
        "network": False,
        "release_approved": False,
    }
    files[MANIFEST] = (json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(output, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False) as archive:
                for name in sorted(files):
                    archive.writestr(_info(name), files[name])
            stream.flush()
            os.fsync(stream.fileno())
        digest = verify_archive(output)
        fd = os.open(sidecar, flags, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(f"{digest}  {output.name}\n".encode("ascii"))
            stream.flush()
            os.fsync(stream.fileno())
        return output, digest
    except BaseException:
        # No recursive deletion or automatic artifact overwrite. Failed output
        # remains available for owner inspection, with no release-ready claim.
        raise


def verify_archive(path: Path) -> str:
    """Validate exact expected source members, sizes, duplicate names and hashes."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE:
        raise InputError("unsafe, missing, or oversized archive")
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            if len(names) != len(set(names)) or set(names) != _expected():
                raise InputError("unexpected, missing or duplicate archive members")
            decoded: dict[str, bytes] = {}
            for info in zf.infolist():
                if info.is_dir() or info.file_size > MAX_MEMBER or info.compress_size > MAX_MEMBER:
                    raise InputError("unsafe archive member")
                if info.filename.startswith("/") or "\\" in info.filename or ".." in info.filename.split("/"):
                    raise InputError("archive path traversal")
                decoded[info.filename] = zf.read(info.filename)
        obj = json.loads(decoded[MANIFEST].decode("utf-8"))
        if (not isinstance(obj, dict) or obj.get("format") != "flowpilot-universal-pyz-v1"
                or obj.get("min_python") != "3.11" or obj.get("network") is not False
                or obj.get("release_approved") is not False
                or set(obj.get("entries", {})) != (_expected() - {MANIFEST})):
            raise InputError("invalid or unsupported package manifest")
        if decoded[ROOT_MAIN] != ENTRY.encode("utf-8"):
            raise InputError("package entrypoint has changed")
        for name, expected in obj["entries"].items():
            if not isinstance(expected, str) or _digest(decoded[name]) != expected:
                raise InputError("package source digest mismatch")
        return _digest(path.read_bytes())
    except (zipfile.BadZipFile, ValueError, UnicodeError, json.JSONDecodeError, KeyError) as exc:
        raise InputError("invalid or damaged portable archive") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FlowPilot first-party offline Python zipapp packager")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--build", type=Path, help="New .pyz path (outside product source)")
    actions.add_argument("--verify", type=Path, help="Read-only verify an existing .pyz")
    opts = parser.parse_args(argv)
    try:
        if opts.verify:
            digest = verify_archive(opts.verify)
            print(f"VERIFIED SHA256 {digest} {opts.verify.name}")
        else:
            src = Path(__file__).resolve().parent.parent
            output, digest = build_archive(src, opts.build)
            print(f"CREATE_ONLY SHA256 {digest} {output} (requires Python 3.11+; NOT EXE)")
        return 0
    except (OSError, InputError) as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
