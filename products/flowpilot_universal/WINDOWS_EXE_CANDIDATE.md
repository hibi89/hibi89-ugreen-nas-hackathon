# FlowPilot Universal P85 Windows executable candidate (private CI-only)

- Source: `products/flowpilot_universal/desktop_entry.py`; workflow `.github/workflows/flowpilot-universal-exe.yml` on the isolated product branch.
- Build: PyInstaller 6.22.3 pinned on GitHub Actions Windows runner, Python 3.11, `--onedir --windowed` with the bundled Tkinter GUI. The result is a folder containing `FlowPilotUniversal.exe` and dependencies. A single EXE copied out of this folder alone may not run.
- Test: run **the generated EXE** with `--self-test`; synthetic temporary source and manifest, actual Tk root+App initialization, read-only SHA scan, SQLite history, JSON+HTML evidence re-verification, no source mutation; no customer data or NAS credentials.
- The CI does **not publish, upload, attach, release, sell or distribute** binaries. It only logs SHA256 inside the build job. The resulting candidate is **unsigned** and has not been checked on a physical buyer Windows 10/11 PC.
- PyInstaller official GPL exception generally permits bundling commercial applications subject to third-party dependency license terms. That is not a substitute for an independent release license review (Python/Tcl/Tk, bundled libraries, NOTICE and warranty obligations).
- PyInstaller packages are fetched by the CI runner for an internal development build; this workflow does not upload customer files or send local source/data to a third-party AI service. CI minute consumption and GitHub-hosted execution remain subject to repo quota.
- Reproduce only from the approved product branch with a clean environment; do not download a candidate for customer use, sign it, change permission or approve sale without owner approval.
- Signed EXE/installer, antivirus/SmartScreen, Win10/11 physical user test, USB and authorized SMB NAS remains NOT VERIFIED. Final overall 85% remains UNASSESSED until entire approved design is independently scored.
