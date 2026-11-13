"""CLI: python -m flowpilot_universal --root ... --manifest ... --json ... [--html ...]."""
import argparse
import json
import sys
from pathlib import Path
from .engine import InputError, create_only, load_manifest, render_html, scan

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local-only read-only file delivery verification")
    parser.add_argument("--root", type=Path, required=True, help="Explicitly authorized local/OS-mounted share directory")
    parser.add_argument("--manifest", type=Path, required=True, help="Requirements JSON schema v1")
    parser.add_argument("--json", type=Path, required=True, help="New JSON report path (never overwrites)")
    parser.add_argument("--html", type=Path, help="Optional new HTML report path")
    opts = parser.parse_args(argv)
    try:
        manifest = load_manifest(opts.manifest)
        output_paths = [opts.json] + ([opts.html] if opts.html else [])
        if len({str(p.absolute()) for p in output_paths}) != len(output_paths):
            raise InputError("report targets must be different")
        for target in output_paths:
            if target.exists() or target.is_symlink():
                raise InputError("refusing to overwrite existing report")
            parent = target.absolute().parent.resolve(strict=True)
            root = opts.root.resolve(strict=True)
            if parent == root or root in parent.parents:
                raise InputError("cannot save report inside inspected root")
        result = scan(opts.root, manifest)
        create_only(opts.json, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", opts.root)
        if opts.html:
            create_only(opts.html, render_html(result), opts.root)
        print(f"{result['status']} scanned={result['files_scanned']} issues={len(result['issues'])}")
        return 0 if result["status"] == "READY" else 2
    except (InputError, OSError) as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
