# G4 early prototype — conservative combined report (2026-10-24)
Status: **OFFLINE CODE + SYNTHETIC TESTS ONLY**. This report composes existing G2 presence checks, G3b version signals, and G3c permission eligibility into one output with `BLOCKED / NEEDS_REVIEW`. It intentionally does **not** produce `READY`, because the actual official SDK version-verification and sensitive-content security checks are still NOT_CHECKED.

Source: `src/projectready/combined_report.py`, unit tests `tests/test_combined_report.py`. Mock SDK_VERIFIED arguments in tests are simulated contract fixtures and cannot authorize real customer NAS reads. Report results are not legally/technically authoritative. Production integration must wait for exact documented registered Expert Agent / supported UGOS CLI input-output conventions, permissions and official checker. Python is development-only and must not be included in official Round 1 submission ZIP.

The existing Round 1 internal schedule retains 11/03-04 for actual supported Uliya Skill integration. Avoid repeating the already tested local core logic. No sensitive user content, paid API, NAS I/O or external transfer was performed.
