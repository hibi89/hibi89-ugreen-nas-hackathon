# FlowPilot Universal P85 — approved-checklist GUI, NTFS junction safety, relocated EXE candidate evidence

Checked 2026-11-13 KST. **Final owner target: verified 85% of unchanged F01–F10 whole design. Official percentage UNASSESSED; 85% NOT CERTIFIED; [작업중] remains; RELEASE HOLD and customer sale NO-GO.**

## Verified source / exact GitHub Actions proof

- Repo `hibi89/hibi89-ugreen-nas-hackathon@product/flowpilot-universal`; functional SHA **`458673ddbec8102dadc04c45ffe1a03f646c119a`** (includes 2026-11-13 previous PDF/security functionality).
- [Full offline CI #43395109341](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43395109341) at exact SHA, **2/2 jobs SUCCESS**, Python3.11 compileall PASS on both platforms. **Windows hosted:** 94/94 distinct unittest PASS, including **three real Windows NTFS `mklink /J` junction tests PASS** (nested junction not traversed, source junction rejected, output junction rejected). **Ubuntu:** 91 PASS, 3 Windows-only tests explicitly SKIPPED. Separate repeat of 8 portable tests PASS per OS (subset already counted), real Tk GUI widget/event-loop **5 scenarios PASS per OS**. All synthetic local data; no customer NAS.
- [Full owner-blueprint policy #43395109927](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43395109927) SUCCESS (policy check, not percentage certification).
- [Private unsigned Windows EXE/ZIP candidate #43395109335](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43395109335) at exact functional SHA: pinned PyInstaller 6.22.3 + optional Korean PDF package, `--onedir --windowed` actual `FlowPilotUniversal.exe --self-test` **EXIT 0**; SHA256-manifest ZIP created, checked, extracted to fresh directory, then relocated executable `--self-test` with developer Python environment removed from PATH **EXIT 0**. ZIP SHA256 `a13ba67da7bc911f3395522ddfb7027134f930e8198166bd82ae0a1b752b79cf`; EXE SHA256 `AF408CFE0028DE62F5C873C1A1BCA0C300D0AB7B49FB8CFD4EDBE7D814A22B3D`. **Unsigned, onedir (requires dependency folder), no artifact uploaded, released, signed, customer distributed, or run on physical customer Windows10/11.** These hashes correspond only to this ephemeral exact CI build.

## New product functions

### F02 — independently authored manifest checklist GUI

`flowpilot_universal/manifest_editor.py` and Tk `GUI.open_template_editor` provide an offline form to type required relative delivery paths and optional TAB-separated SHA256 digests. `render_manifest(..., approved=True)` and `create_approved_manifest` enforce explicit operator acknowledgement that the list comes from independent contract/requirements; scanner source is **never used to auto-fill its own expected contents**. The GUI only allows save after approval, chooses a new JSON filename outside the original authorized folder, writes with create-only `O_EXCL`, refuses duplicates/casefold collisions, path traversal, Windows invalid names, invalid/overlong hashes, oversized lists and symlink outputs. Newly saved schema-v1 JSON is ready for the original scanner. **This is a form/editor, not a curated industry contract template library and not real customer/contract sign-off.**

Two designs compared: (A) generate required files from current source automatically, faster but tautologically accepts missing customer deliverables; (B) owner-supplied requirements independently approved before save, more manual work but valid audit authority. **B chosen.**

### F05 — actual Windows NTFS junction boundary

The original `Path.is_symlink()` preflight might not reject a Windows junction because an NTFS junction is a reparse point, not always reported as a symbolic link. Root and output preflights now use `lstat` + `FILE_ATTRIBUTE_REPARSE_POINT`; nested junction already yielded `UNSAFE_LINK`/INCOMPLETE. Three actual `mklink /J` tests PASS on Windows hosted CI with independent temporary data and no share/user permission modifications. **This proves tested junction cases only; not all Windows ACL/SMB races or immutable snapshots.**

### F08 — complete local onedir candidate relocation test

`verify_delivery_archive.py` creates a new ZIP from the EXE+dependencies folder, refuses source symlinks, missing EXE, file/size cap breaches, existing ZIP overwrite, verifies per-member SHA256 and a local index before extracting into a brand-new directory. Negative ZIP tamper/traversal tests PASS, and the **actual packaged EXE is invoked from the relocated folder with a sanitized PATH**. SHA manifests prevent accidental/casual modification, **not coordinated malicious rewrite or cryptographic publisher authentication**. CI retains no distributable, creates no GitHub Releases and does not alter Vercel, certificate stores or user environments.

## Failures, diagnosis and recovery

- [Initial source CI #43394045445](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43394045445): unit suite 91 passed but GUI smoke aborted in Linux/Windows with `Tcl_AsyncDelete: async handler deleted by the wrong thread` after recently introduced editor windows. Changed GUI to release child Tk variables/widget references on the owning Tk thread, explicit edit-window WM_DELETE callback; GUI smoke `tearDown` now drains/joins worker and collects on UI thread. [Second-source CI #43394490099](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43394490099) Linux/Windows 91 + Tk5 each SUCCESS. No hollow reruns; real defect addressed.
- Latest #43395109341 adds root/output NTFS reparse defenses and real junction regression SUCCESS; EXE/archive #43395109335 also SUCCESS. Pre-change product HEAD `d2db1d70d95a6733cd83a9bf80acf68a7b5cecfc` is available in Git history. Do not delete original customer evidence on rollback.

## Remaining owner-85 and commercial blockers

Full blueprint F01–F10 retains unverified independent acceptance: physical buyer Windows10/11 (actual USB/local folders, customer permissions), explicitly approved real OS-mounted UNC SMB NAS (multi-vendor), high-volume and adversarial network filesystem races, legally approved signed installer/SmartScreen/AV, font/third-party license/NOTICE, support/retention/contract/customer sign-off, and **owner-approved 100-point requirement weighting**. Distinguish synthetic hosted CI from consumer hardware. P85 milestone names/test counts never establish certified final completion percentage. **No externally authorized NAS access or credentials were used**, no customer data uploads/payments/release. UGREEN `lead/ugreen`, `main`, official Skill, external deployment and unrelated Kmong products unchanged.

## Reproduction

From `products/flowpilot_universal` with Python3.11:
```sh
python -m unittest discover -s tests -p 'test_*.py' -v
python -m unittest discover -s tests -p 'test_portable.py' -v
python -m compileall -q flowpilot_universal
python -m flowpilot_universal.gui
```
Optional Korean PDF CI installs `reportlab==4.4.9`, `pypdf==6.1.3` for tests and a local licensed Korean TTF. Private Windows EXE workflow packages only a synthetic-testable candidate, and deliberately contains no upload/release step. For each real customer sample require separate consent, QA logs, root/report snapshots and no claims of broad device support.
