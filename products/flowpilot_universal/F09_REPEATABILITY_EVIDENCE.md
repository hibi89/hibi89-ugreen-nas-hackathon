# FlowPilot Universal F09 — operator-initiated repeatability evidence, NOT physical acceptance

**2026-11-14 KST**, code and tests `b723544735cffcf2d05c19773e5ed04336d26e7a`.
[Exact source CI #43506736478](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43506736478): **Windows Python3.11 109/109 PASS**, **Ubuntu Python3.11 102 PASS + 7 Windows-only SKIP**, 0FAIL, actual Tk5/OS and portable8 rerun/OS, compileall, 2/2 SUCCESS. [Completion policy #43506737121](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43506737121) SUCCESS is policy only.

## Design choice, scope and commands

- A = manually repeat Tk scan 3 times. Free, no code, but human comparison is error-prone.
- B = separate consent-only stdlib CLI wrapping the already-tested `session.run_session` in **three independent full non-resumed SHA scans** and SQLite JSON+HTML verification, cross-round file digest comparison. B chosen for auditability and no new dependency/permission/paid API.
- From `products/flowpilot_universal`, after *independently* obtaining legal source access and approved manifest:
  `python -m flowpilot_universal.field_trial --root <already-accessible-folder> --manifest <approved-requirements.json> --output <existing-folder-outside-source> --medium pc --consent`.
  `--medium` accepts `pc`, `usb`, `smb` and is an **unverified operator assertion**. Never auto-discover/mount shares; do not enter credentials or collect customer files in chat.
- Create-only local `flowpilot-field-trial-*.json` stores manifest hash, per-round session id, local report SHA, SHA of canonical file paths/sizes/hashes. `REPEATABILITY_PASS_NOT_FIELD_ACCEPTANCE` means **selected local scope stable over exactly three scans only**. Non-READY report, changed bytes/list, changed manifest or failed report verification => `INCOMPLETE` (evidence left for review).
- Existing source files remain read-only; evidence saved outside the source in selected output; no data upload, hosted server, NAS action or API charge. Three passes can read up to 3× the configured per-scan byte limit, so operator should size-check their allowed folder first.

## Evidence and unverified limits

New `tests/test_field_trial.py` has seven focused synthetic cases: consent gate/CLI, three stable rounds, missing contract, source changed between scans, manifest changed, tamper verification failure, in-source output & invalid medium. 109/109 hosted Windows and Linux102+7SKIP regression **does not constitute physical buyer acceptance**. The trial does not verify Windows physical version, actual USB identity, NAS brand, UNC SMB ownership, share ACL, immutable snapshot, adversarial SMB race, commercial font/PyInstaller/installer license, certificate/SmartScreen, EULA, support/refund, or buyer sign-off.

**Formal final F01–F10 completion:** owner-approved 100-point weights and physical acceptance still missing, **UNASSESSED**. No percentage 85 claimed. Keep `[작업중]` and SALE/RELEASE HOLD, preserve UGREEN `lead/ugreen`/main and all other products. Previous product HEAD `4aaffbd700a249f130660fb9b3e4d35d1c48537d` is the pre-task recovery reference; source `b723544735cffcf2d05c19773e5ed04336d26e7a` is the verified functionality rollback point.
