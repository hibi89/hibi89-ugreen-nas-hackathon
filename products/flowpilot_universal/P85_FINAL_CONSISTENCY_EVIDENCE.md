# FlowPilot Universal — P85 end-of-scan consistency & Windows reparse guard evidence

**Verified: 2026-11-14 KST**. Target is **85% of unchanged full F01–F10 owner blueprint**. Technical progress does **not** establish the official percentage. Owner-approved total-100 requirement weights and real buyer acceptance still missing: **official completion UNASSESSED, 85% NOT CERTIFIED, [작업중] retained, RELEASE HOLD**.

## Source, CI, scope

- Repository: `hibi89/hibi89-ugreen-nas-hackathon@product/flowpilot-universal`.
- Exact functional source SHA: `bd74a05fcacc426a101c070beaaad49e54283cbe`.
- [Linux/Windows CI #43500327638](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43500327638) at this SHA: 2/2 jobs SUCCESS, Python3.11 `python -m unittest discover -s tests -p 'test_*.py' -v`; Windows 102/102 PASS, 0 FAIL, 0 SKIP; Ubuntu 95 PASS / 7 SKIP for Windows-only NTFS junction checks. Separate 8/8 portable test rerun per OS (duplicate subset, not 8 additional unique cases), real Tk widget/event-loop 5/5 PASS per OS, Python `compileall` PASS.
- [Final-blueprint policy #43500328207](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43500328207) SUCCESS at SHA (policy check only, not official full-product acceptance).
- [Private Windows EXE & relocated ZIP #43500327639](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43500327639) SUCCESS at same SHA: PyInstaller pinned 6.22.3, `FlowPilotUniversal.exe --self-test` **EXIT 0**, SHA256-indexed create-only bundle ZIP verified, relocated extraction to new directory, development Python removed from PATH, relocated `FlowPilotUniversal.exe --self-test` **EXIT 0**. Temporary candidate ZIP SHA256 `b2000468b97a3d445cf2f1de69f735699398881041dd59894037a47c56d2fde4`; built EXE SHA256 `0789659E776E15357A5B86A9B1AE55EAB308C3F1A42A64C141D851B695563349`. These hashes identify the temporary runner artifacts **not published, signed or available for commercial download**.

## F03/F05 consistency improvement

The scanner previously bounded the scan and checked each file before/after hashing and directories after listing. It could still miss a **previously hashed file being modified later while scanning another file**. Implemented a **final best-effort source recheck** before creating a READY report:

- Store metadata fingerprints for each successfully hashed file and initially scanned directories; after the scan re-list directory names shallow-first and lstat regular files; if an earlier file, directory name set, type, link status or size/mtime changes, add `FILE_CHANGED_AFTER_SCAN` or `DIRECTORY_CHANGED_FINAL` and return **INCOMPLETE**.
- Recheck is bounded by the existing 20,000-file/25,000-directory caps and obeys user cancellation. No extra writes to source. Report PDF/JSON/HTML will represent an incomplete audit rather than false READY when a detectable change occurs.
- New `tests/test_final_consistency.py` covers earlier file modified after its SHA, later directory addition, unchanged READY/session, and nested directory late change.
- Original cancellation, partial file read, resume `NEEDS_REVIEW` and full rehash READY policies unchanged. Cached SHA is **never trusted** to make READY.

**Security limit:** This is not an immutable/atomic filesystem snapshot or authenticated hostile SMB source. Metadata-preserving edits, changes after the final pass, reparse/ACL races and network-side changes may evade detection. Real authorized UNC SMB NAS test remains required.

## F05 output and evidence paths

A Windows NTFS junction is a reparse point and may not be reported by `Path.is_symlink()`. Source and output entrypoints were already guarded. This revision also guards lower-level paths used independently:

- `engine.create_only`: source and destination parent reparse rejection, `os.path.lexists` for preexisting/broken link destinations, still O_EXCL create-only and outside-source enforcement.
- `session._history_connection`, `backup_history`, `verify_history_entry`: reject reparse history file or history output root; original database remains intact.
- `checkpoint.ResumeCheckpoint`: reject junction source or output folder (not just POSIX symlinks).
- `pdf_report.create_pdf_only`: reject junction parent folder.
- Extended real Windows hosted `mklink /J` regression `tests/test_ntfs_junction.py`: four additional cases (create-only output, direct PDF output, checkpoint root/output and history backup/verify) PASS without requiring user NAS hardware, permissions or external sharing. Older three original junction tests still PASS. Ubuntu skips all seven Windows-only checks explicitly.

## Remaining product acceptance, cost, recovery and next actions

- The original F01–F10 final blueprint scope has **not changed**. F02 owner-approved checklist/Tk editor, F03 SHA, F04 duplicates/version, F05 path safety, F06 JSON/HTML/Korean PDF/SQLite, F07 resume+GUI, F08 unsigned relocated EXE are internally tested but **not buyer-accepted**.
- F09 physical customer Windows10/11, actual USB/portable drives, owner-authorized two-vendor UNC SMB NAS and file permission/adversarial race/large workload E2E are NOT RUN. F10 commercial rights/third-party font NOTICE, executable code-signing/installer and AV/SmartScreen, retention/support/refund and buyer acceptance/ship approval NOT DONE. A user-approved whole-design weighted 100-point score still does not exist; do not assign official 85%.
- No paid API, customer data upload, live NAS, GitHub Release, deployment permission/branch protection or code-signing changes. Windows EXE created only temporarily in GitHub runner, no attachment uploaded. CI usage is bounded by existing GitHub quota; no claim of no CI quota cost.
- Before this change, product branch HEAD was `44301fd666fd89bff4339b36b3bf30641dea977e`, retained in Git history for selective revert. Do not delete original local reports, SQLite backups or customer files; UGREEN `lead/ugreen`, `main`, contest Skill/submission and other products unchanged.
- Next: physical Win10/11/USB/authorized NAS owner-run evidence, validated installer/signature/rights, independent final F01–F10 acceptance matrix and approved weights before official completion/market release. **Keep [작업중] and RELEASE HOLD.**
