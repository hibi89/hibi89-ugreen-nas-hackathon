# UGREEN Windows launcher path normalization — 2026-10-30

Three PowerShell scripts now resolve relative source roots against the actual
UGREEN checkout directory (parent of tools/), not the shell's current working
directory. Absolute paths are preserved and normalized. The suite's optional
relative output path is also anchored to the checkout, avoiding user-folder
dependent behavior from launchers and shortcuts.

Defaults: sibling directories ../HAE, ../SOVIA_sovereign, ../DBVORA.
None of the launchers fetches, checks out or modifies private sources.
Synthetic SQLite writes still require an explicit approval switch.
Four source-code tests check these static PowerShell invariants, but do not
claim that a Windows interpreter was run in public Linux CI.

Example from any Windows shell directory:
  powershell -NoProfile -File C:\path\UGREEN\tools\run_four_source_doctor.ps1

Expected checkout SHA and clean worktree are verified by the Python doctor;
actual NAS/Uliya use and official Creator evidence remain unverified.
