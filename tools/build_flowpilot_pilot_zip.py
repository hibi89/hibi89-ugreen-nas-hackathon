"""Build a genuinely offline, reproducible FlowPilot LOCAL pilot ZIP.

Accepts no customer paths beyond the developer-selected destination ZIP.
Only source files required by the two entrypoints and three fixed Windows
launchers are packed. Builds after actual four-capability acceptance PASS.
Never contains private HAE/SOVIA/DBVORA repositories, NAS data or credentials.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[1]
PREFIX = "FlowPilot_Local_Pilot"
SOURCE_ENTRYPOINTS = (
    "tools/flowpilot_four_source_local_ui.py",
    "tools/flowpilot_local_acceptance.py",
)
OTHER_FILES = (
    "tools/START_FLOWPILOT_DEMO.cmd",
    "tools/VERIFY_FLOWPILOT_LOCAL_MVP.cmd",
    "OWNER_LOCAL_PILOT_QUICKSTART.md",
)
DENIED_PARTS = {
    ".git", ".github", ".env", ".venv", "__pycache__", ".pytest_cache",
    "evidence", "secrets", "tokens",
}
MAX_FILE = 400_000
MAX_BUNDLE = 5_000_000


class PilotBundleRefused(ValueError):
    """Only safe static reason strings. Do not disclose local paths."""


def _safe_file(root: Path, relative: str) -> Path:
    path = Path(relative)
    if (not relative or path.is_absolute() or ".." in path.parts
            or any(part.lower() in DENIED_PARTS for part in path.parts)
            or any(part.startswith(".") for part in path.parts)):
        raise PilotBundleRefused("UNSAFE_BUNDLE_FILE")
    full = root / path
    if (not full.is_file() or full.is_symlink()
            or any(p.is_symlink() for p in full.parents if p != root.parent)
            or not 0 < full.stat().st_size <= MAX_FILE):
        raise PilotBundleRefused("BUNDLE_FILE_NOT_SAFE")
    return full


def _module_file(root: Path, module: str) -> str | None:
    parts = module.split(".")
    if not parts or any(not p.isidentifier() for p in parts):
        return None
    if parts[0] == "tools":
        rel = "tools/" + "/".join(parts[1:])
    elif parts[0] == "integrations":
        rel = "integrations/" + "/".join(parts[1:])
    elif parts[0] == "flowpilot":
        rel = "src/flowpilot/" + "/".join(parts[1:])
    elif parts[0].startswith("flowpilot_"):
        rel = "tools/" + "/".join(parts)
    else:
        return None
    if module in ("tools", "integrations", "flowpilot"):
        rel = rel.rstrip("/") + "/__init__"
    candidate = rel + ".py"
    return candidate if (root / candidate).is_file() else None


def _dependencies(root: Path, filename: str, data: bytes) -> set[str]:
    try:
        tree = ast.parse(data, filename="<offline-bundle-source>")
    except SyntaxError:
        raise PilotBundleRefused("INVALID_PYTHON_SOURCE") from None
    imports = set()
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.Import):
            modules = [part.name for part in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # flowpilot package-relative imports, if present
                ancestor = filename.replace("/", ".").removesuffix(".py")
                segments = ancestor.split(".")[:-node.level]
                if segments and segments[0] == "src":
                    segments = segments[1:]
                if node.module:
                    modules = [".".join(segments + [node.module])]
                else:
                    modules = [".".join(segments + [part.name]) for part in node.names]
            elif node.module:
                modules = [node.module]
        for module in modules:
            resolved = _module_file(root, module)
            if resolved is not None:
                imports.add(resolved)
            elif (module.startswith(("flowpilot_", "tools.", "integrations.",
                                     "flowpilot."))
                  and not any(module.startswith(prefix) for prefix in (
                      "flowpilot_legacy", ))):
                raise PilotBundleRefused("UNRESOLVED_LOCAL_IMPORT")
    return imports


def _collect(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    queue = list(SOURCE_ENTRYPOINTS)
    while queue:
        name = queue.pop(0)
        if name in files:
            continue
        source = _safe_file(root, name)
        if not name.endswith(".py"):
            raise PilotBundleRefused("NON_PYTHON_DEPENDENCY")
        data = source.read_bytes()
        files[name] = data
        queue.extend(sorted(_dependencies(root, name, data) - files.keys()))
        if sum(len(v) for v in files.values()) > MAX_BUNDLE:
            raise PilotBundleRefused("BUNDLE_SOURCE_SIZE_EXCEEDED")
    for name in OTHER_FILES:
        files[name] = _safe_file(root, name).read_bytes()
    # Include local package markers when present.
    for marker in ("tools/__init__.py", "integrations/__init__.py",
                   "src/flowpilot/__init__.py"):
        if (root / marker).is_file() and marker not in files:
            files[marker] = _safe_file(root, marker).read_bytes()
    if sum(len(v) for v in files.values()) > MAX_BUNDLE:
        raise PilotBundleRefused("BUNDLE_SOURCE_SIZE_EXCEEDED")
    return dict(sorted(files.items()))


def _accept(root: Path) -> None:
    try:
        result = subprocess.run(
            [sys.executable, str(root / "tools" / "flowpilot_local_acceptance.py")],
            cwd=root, capture_output=True, text=True, timeout=90, check=False,
        )
        report = json.loads(result.stdout)
        if (result.returncode != 0
                or report.get("status") != "PASS_FOUR_LOCAL_CAPABILITY_CHECKS"
                or report.get("passed") != 4
                or report.get("failed") != 0
                or report.get("generated_disposable_test_data_only") is not True
                or report.get("actual_nas_verified") is not False
                or report.get("release_gate") != "HOLD"):
            raise PilotBundleRefused("FOUR_CAPABILITY_ACCEPTANCE_NOT_PASS")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise PilotBundleRefused("FOUR_CAPABILITY_ACCEPTANCE_NOT_PASS") from None


def _write_zip(target: Path, files: dict[str, bytes]) -> dict:
    if not target.is_absolute() or target.suffix.lower() != ".zip":
        raise PilotBundleRefused("ABSOLUTE_ZIP_PATH_REQUIRED")
    if target.exists() or target.is_symlink() or not target.parent.is_dir():
        raise PilotBundleRefused("ZIP_DESTINATION_OCCUPIED_OR_MISSING")
    manifest = {
        "schema": "flowpilot-offline-local-pilot-v1",
        "scope": "FOUR_REAL_LOCAL_CAPABILITIES_ONLY",
        "files": {name: hashlib.sha256(data).hexdigest()
                  for name, data in files.items()},
        "source_file_count": len(files),
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "official_creator_verified": False,
        "release_gate": "HOLD",
    }
    payloads = dict(files)
    payloads["MANIFEST.json"] = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    created = False
    try:
        # Exclusive creation: only clean up a file THIS process created.
        # A racing external creator's file must never be deleted.
        with target.open("xb") as handle:
            created = True
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=9) as archive:
                for name, data in sorted(payloads.items()):
                    entry = zipfile.ZipInfo(f"{PREFIX}/{name}", (1980, 1, 1, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    entry.external_attr = 0o644 << 16
                    archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED)
    except Exception:
        if created and target.is_file():
            target.unlink()
        raise PilotBundleRefused("ZIP_BUILD_FAILED") from None
    return {
        "status": "OFFLINE_LOCAL_PILOT_ZIP_BUILT",
        "source_file_count": len(files),
        "zip_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "bundle_contains_owner_files": False,
        "four_capability_acceptance_passed_before_build": True,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "release_gate": "HOLD",
    }


def build_offline_pilot(out: Path, *, root: Path = REPO) -> dict:
    _accept(root)
    return _write_zip(out, _collect(root))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="4-capability offline local pilot ZIP, NOT NAS")
    p.add_argument("--out", type=Path, required=True,
                   help="New absolute .zip path; existing files are never overwritten")
    args = p.parse_args(argv)
    try:
        print(json.dumps(build_offline_pilot(args.out), sort_keys=True))
        return 0
    except (PilotBundleRefused, OSError, ValueError, TypeError):
        print(json.dumps({"status": "OFFLINE_PILOT_BUILD_REFUSED",
                          "actual_nas_verified": False, "release_gate": "HOLD"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
