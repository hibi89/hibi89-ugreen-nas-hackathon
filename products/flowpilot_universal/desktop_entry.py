"""FlowPilot Universal Windows EXE candidate entrypoint.

PyInstaller can bundle this with --onedir --windowed. No network or NAS control.
The --self-test mode uses synthetic temporary files and never customer data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile


def self_test() -> int:
    import tkinter as tk
    from flowpilot_universal.gui import App
    from flowpilot_universal.session import run_session, verify_history_entry
    try:
        with tempfile.TemporaryDirectory(prefix="flowpilot-exe-smoke-") as tmp:
            base = Path(tmp)
            source = base / "synthetic-source"
            out = base / "synthetic-reports"
            source.mkdir()
            out.mkdir()
            content = b"synthetic-evidence-only"
            (source / "document.dat").write_bytes(content)
            manifest = base / "requirements.json"
            manifest.write_text(
                json.dumps({"schema_version": 1, "expected_files": [{
                    "path": "document.dat", "sha256": hashlib.sha256(content).hexdigest()
                }]}),
                encoding="utf-8",
            )
            window = tk.Tk()
            window.withdraw()
            try:
                app = App(window)
                app.root.set(str(source))
                app.output.set(str(out))
                app.manifest.set(str(manifest))
                window.update()
                result = run_session(source, manifest, out, consent=True)
                if result.status != "READY":
                    return 10
                proof = verify_history_entry(out, result.session_id)
                if proof["reports_verified"] != 2:
                    return 11
                if (source / "document.dat").read_bytes() != content:
                    return 12
            finally:
                window.destroy()
    except Exception as exc:
        # GUI Windows executable has no stderr console; return failure to CI.
        try:
            if sys.stderr is not None:
                print(f"EXE SMOKE HOLD: {exc}", file=sys.stderr)
        except OSError:
            pass
        return 1
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        return self_test()
    if argv == ["--help"]:
        if sys.stdout is not None:
            print("FlowPilot Universal offline GUI. Use --self-test only for synthetic CI.")
        return 0
    if argv:
        return 2
    from flowpilot_universal.gui import main as launch
    launch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
