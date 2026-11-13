# [2026-11-14] Windowed Windows EXE now supports F09 three-pass offline trial (still not buyer-accepted)

- `FlowPilotUniversal.exe --field-trial --root <authorized> --manifest <approved.json> --output <separate-existing-folder> --medium pc --consent` invokes 3 complete no-cache SHA scans, verifies local JSON/HTML/SQLite and saves a new local trial summary; CLI is bundled in the existing unsigned onedir EXE (no developer Python). With a `--windowed` executable **no terminal output is expected**; read the created `flowpilot-field-trial-*.json` and process exit code. Do not scan any folder without legal access and explicit scope approval.
- Source `e8bc4f318087bd83634f9f177e73fbc87e43a95f`: [full Windows/Linux CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43511163767) Win111 PASS/Linux104 PASS+7 Win-only SKIP, GUI5 and portable8/OS. [Actual bundled Windows EXE CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43511163790) initial, ZIP-relocated, installed `--self-test` EXIT0; new self-test includes F09 path+no-consent check. No public binary/upload/customer hardware. [Technical evidence and zero-cost F10 rights preflight](F08_F09_EXE_AND_F10_RIGHTS_20261114.md).
- Original final F01–F10 scope fixed. Actual Win10/11·USB·2-vendor NAS, license/NOTICE/signing/customer legal acceptance and owner-approved total-100 weights missing: **official UNASSESSED, target 85 NOT CERTIFIED, [작업중], RELEASE HOLD.**

---

# 2026-11-14 KST — F09 three-pass offline field-readiness CLI (not hardware acceptance)

- Run only against an **already accessible and authorized** local/USB/OS-mounted SMB folder with an independently approved manifest, using a separate existing output folder: `python -m flowpilot_universal.field_trial --root <approved-folder> --manifest <requirements.json> --output <existing-outside-source-folder> --medium pc --consent` (choose `pc`, `usb`, or `smb`; media labels are operator claims, not device proofs).
- Performs up to **three full uncached SHA rehash scans**, SQLite-backed JSON+HTML verification, manifest immutability check, cross-round file/size/SHA parity, and a create-only local JSON summary. Non-READY, changed contents or invalid evidence => **INCOMPLETE**; no file write inside source, NAS discovery, mount or external upload.
- [Full Linux/Windows source CI #43506736478](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43506736478) at code `b723544735cffcf2d05c19773e5ed04336d26e7a`: Windows **109 PASS**, Ubuntu **102 PASS + 7 Windows-only SKIP**, real Tk5 + portable8 rerun/OS, 2/2 SUCCESS. Seven new field-trial regression tests. [Policy](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43506737121) SUCCESS, policy only. [Limits and recovery](F09_REPEATABILITY_EVIDENCE.md).
- No physical customer Windows10/11, real USB, authorized multi-vendor SMB NAS, code signing, licensing, buyer sign-off, or approved full F01–F10 100-point weights. **Official UNASSESSED, final 85% NOT CERTIFIED, [작업중], RELEASE HOLD.**

---

# [2026-11-14 KST] Windows offline installation and safe-uninstall rehearsal, not a public installer

- `windows_candidate_install_rehearsal.ps1` works **only in a direct child of GitHub Actions `RUNNER_TEMP`**, intentionally rejects buyer PCs/other folders. This is a no-admin/no-registry/offline synthetic test, not an installer artifact or user-facing setup script. [Actual Windows hosted CI #43504574468](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43504574468) pass: candidate ZIP checksum, extracted EXE runtime exit0, unexpected customer file blocks uninstall, clean uninstall verified. Candidate unsigned and not uploaded/distributed.
- [Linux/Windows full regressions #43504574472](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43504574472): Windows102 PASS, Linux95 PASS+7 Windows-only SKIP, live Tk5 PASS/OS, portable8 repeated/OS.
- [Owner-wide F01–F10 completion acceptance matrix](FINAL_BLUEPRINT_85_ACCEPTANCE_MATRIX.md) distinguishes verifiable CI functions from the unapproved whole-final-design weights, actual physical Windows10/11/USB/authorized SMB NAS, signed installer and rights/customer acceptance. **Official final rate UNASSESSED; target 85% NOT CERTIFIED, [작업중] and RELEASE HOLD**. Previous instructions retained below.

---

# LATEST 2026-11-14 KST — final source consistency recheck and NTFS evidence path guard

- [Exact evidence](P85_FINAL_CONSISTENCY_EVIDENCE.md); [Linux/Windows CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43500327638) Windows 102 PASS, Linux 95 PASS and Windows-only NTFS 7 SKIP, Tk real GUI5/OS, portable8 repeated/OS; [private Windows EXE](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43500327639) unsigned bundled original/relocated runtime EXIT0. Source SHA `bd74a05fcacc426a101c070beaaad49e54283cbe`.
- Before a **READY** verdict, the scanner now re-lists observed directories and rechecks previously hashed file metadata so detectable late edits/deletions/additions produce **INCOMPLETE**. This is best-effort, not an atomic filesystem snapshot; concurrent metadata-preserving edits and later source changes remain possible.
- Windows NTFS junctions are refused by source/output report generators, SQLite history/backup/verification, checkpoint and PDF creation; seven actual hosted Windows junction test cases PASS. This is not evidence of production NAS ACL or network share access.
- This is a local offline **unsigned** application candidate; physical buyer Windows10/11/USB and authorized multi-vendor UNC SMB, license/signing/customer acceptance and owner approved full 100-point weights still missing. **Official final completion UNASSESSED, 85% NOT CERTIFIED, [작업중] + RELEASE HOLD**. Old setup instructions below remain historical.

---

# LATEST 2026-11-13 KST — owner-approved checklist editor, NTFS junction proof, relocated Windows EXE

- [Evidence](P85_GUI_NTFS_RELOCATED_EVIDENCE.md) / [Linux+Windows CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43395109341) Windows **94 PASS**, Linux **91 PASS + 3 Windows-only SKIP**, real Tk 5 PASS/OS, portable 8 repeated PASS/OS; [Windows EXE+ZIP](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43395109335) `EXE_EXIT 0` + `RELOCATED_EXE_EXIT 0`; user target full design 85% still **UNASSESSED**, RELEASE HOLD, [작업중] remains.
- **GUI → 납품 요구사항 JSON 직접 작성**: select authorized source directory first; type independent delivery paths (one `folder/file.txt` per line) and optional TAB + 64-char SHA-256. Confirm you have independently approved the contract/checklist, then save to a **NEW .json OUTSIDE source**. Existing file will not be overwritten; no scan is used to auto-generate its own requirements. GUI sets new JSON as selected manifest; separately confirm source scan permission before scanning. This editor is not a pre-approved real customer template library.
- **Security and packaging**: original source still read-only; Windows hosted NTFS junction source/root/output rejection tested; Windows unsigned onedir candidate ZIP verified and re-executed after relocation with Python removed from PATH. **No signed installer, ZIP download artifact, actual customer PC/USB/NAS, commercial rights or deployment.**

---

# Latest 2026-11-13 KST — Korean PDF evidence and Windows GUI candidate

- **Evidence:** [full Linux+Windows CI #43391290337](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43391290337) at code `e87f5a2debe445bf749b3466b6a6f19b2febee7d`: **71 unique PASS per OS, 8 portable repeated per OS, 3 live Tk widget PASS per OS**. [Windows EXE PDF runtime #43391157492](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43391157492) EXIT 0; **unsigned / unpublished**. [PDF scope and issues](P85_PDF_EVIDENCE.md).
- **GUI optional PDF:** `python -m flowpilot_universal.gui`, choose authorized source, manifest and separate output, confirm permission, optionally check **한국어 PDF 보고서 추가 생성**. Requires `reportlab==4.4.9` installed in the Python runtime and a locally installed Korean TTF (Windows Malgun Gothic or Linux Nanum). No font included in the repo. Python default scans and `.pyz` without PDF continue with stdlib only. PDF is generated only on explicit checkbox and keeps original source files read-only.
- PDF lists up to 900 files/200 issues with clear truncation warning; complete SHA-256/paths remain JSON. Saved reports can be checked in GUI: optional PDF SHA alongside original JSON/HTML SQLite ledger, 3/3 reports verified; original no-PDF sessions remain 2/2. **Local SHA not a trusted third-party signature.**
- **Limits:** no physical buyer Win10/11/USB/authorized SMB NAS or release/license/font embedding/legal acceptance, installer/signing/SmartScreen. User target 85% **UNASSESSED**, [작업중] + SALE HOLD. Older notes below are historical.

---

# FlowPilot Universal P85 continuation — private CI candidate, release HOLD

- Verified source: `a96e727ba89bb87a4914e85c31da0898ce41c45d`, [Linux/Windows CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387548967) 63 PASS/OS, portable 8 reruns/OS, real Tk widgets 2 PASS/OS; [Windows EXE CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387249760) unsigned PyInstaller onedir GUI executable runtime synthetic `--self-test` EXIT 0 (built at SHA `436d3b635f716d9e2da58a986680cef93edd5374`). **Official final blueprint rate UNASSESSED**, target 85% NOT CERTIFIED, `[작업중]` remains.

## Resume work with explicit caution

In the Tk GUI, check **부분 이어하기** only after granting source scope and permission. Work checkpoint `.flowpilot-resume.sqlite3` stays in selected output (never source), stores completed SHA and source metadata. If stopped, restart with checkbox selected to process remaining files; reused SHA is **not independent proof of current bytes** and produces `NEEDS_REVIEW`. Uncheck resume and start full scan to hash everything for `READY`. Changed manifest/root/foreign DB causes HOLD; use a new output directory to start a different scope. Report backups and original data are preserved. Source directory files are never written.

## Private Windows EXE candidate

PyInstaller 6.22.3 private CI builds `dist/FlowPilotUniversal/FlowPilotUniversal.exe` **plus dependencies in that folder**; no separate Python installation needed for that bundled candidate. Tested Windows GitHub runner `--self-test` GUI+synthetic report flow. It is **unsigned, not uploaded/released, not yet tested on a physical buyer Windows 10/11 PC, not an installer and not approved for sale**. See [build/verification and rights](WINDOWS_EXE_CANDIDATE.md). The original pure-stdlib `.pyz` option still requires customer Python3.11+.

## Official limits

No real customer/SMB/USB NAS acceptance, hardware/model support, native PDF report, signed release, authenticated checkpoint hash, license/support approval or fixed full-100-point rubric. Existing UGREEN competition sources unmodified. Code/CI success is not product ship approval.

---

## Historical P85/P70/P50 reference (earlier TODO statements superseded)

> **2026-11-13 KST P85 개발 증거:** functional SHA `b66ba07b1cef34f0dff7683a9edc5e44684ac852`; [Linux/Windows CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383780676) 각 **55개 고유 테스트 PASS**, portable 8개 재실행/OS PASS, 실제 Tk GUI 1건/OS PASS; 2/2 jobs SUCCESS, 컴파일 검증 PASS. [최종설계 정책 검사](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383781197) SUCCESS. **기술 P85 일부 구현**이나 EXE/설치·실 고객 Windows10/11·USB·SMB NAS·진정한 증분 재개·PDF·상업권·승인된 전체 100점 가중치 미충족. 따라서 **공식 최종완성률 UNASSESSED**, 사용자 목표 85% 미인정, **[작업중]·RELEASE HOLD 유지**. [P85 상세](P85_EVIDENCE.md).
# FlowPilot Universal P85 technical package — Python 3.11+ required

From `products/flowpilot_universal`, build the first-party create-only `.pyz` **outside the product source directory**:

    python -m flowpilot_universal.portable --build /existing-external-folder/NEW-flowpilot.pyz
    python -m flowpilot_universal.portable --verify /existing-external-folder/NEW-flowpilot.pyz
    python /existing-external-folder/NEW-flowpilot.pyz --help
    python /existing-external-folder/NEW-flowpilot.pyz --gui

The example paths are placeholders. Output target and `.sha256` sidecar must be new. `.pyz` needs Python on customer's PC; it is **not a Windows EXE, code signature or installer**. After scanning in the Tk app, select an audit history row and click `선택 이력 검증`: check local JSON SHA and HTML against SQLite audit record; a coordinated editor of both DB and evidence is outside this protection.

Core scan is read-only and offline. Cancel produces `INCOMPLETE`; restart rehashes, not a verified incremental checkpoint. Windows native Tk smoke was run on GitHub-hosted Windows, **not physical buyer Windows10/11**. Production/NAS customer release HOLD. [Evidence](P85_EVIDENCE.md).

---

## Historical P70/P50 instructions

> **2026-11-13 KST additional live Tk proof:** Functional SHA `18273d2c7a9909a5d65bdba4aecc2a8097f9a157`, [GitHub Actions #43380594623](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43380594623) Linux30/30, Windows30/30 PASS and Linux Xvfb actual Tk widget/event-loop consent→scan→history→backup→repeat full scan **1/1 PASS**. This is a synthetic virtual-display desktop interaction, **not** a physical customer Windows10/11 or SMB NAS acceptance. Official rate remains **UNASSESSED**, 70% goal not certified, [작업중] and RELEASE HOLD unchanged.

# FlowPilot Universal — Offline P70 workbench (technical subset; SALE HOLD)

Standalone, local-only delivery QA. This is **not** the UGREEN hackathon Skill, a NAS management agent, or a released Windows executable. It never contacts a service or writes into scanned source folders. Customer filenames, manifest paths and SHA evidence remain sensitive **local** data.

## 1. Native desktop GUI (Python 3.11, standard library)

From `products/flowpilot_universal` on a Windows PC with Python and Tk support:

```powershell
python -m flowpilot_universal.gui
```

Select the authorized PC/USB/OS-mounted SMB directory, select a manifest JSON, choose an **existing output directory outside scanned source**, confirm you have permission via checkbox, then start. Status and local history are shown. Cancel records `INCOMPLETE`. Clicking **새 검수 시작 / 안전한 처음부터 재검사** starts an entirely new SHA scan. **No incremental resume/checkpoint** yet. **이력 백업** creates a new SQLite backup without overwriting prior files; no automatic destructive restore.

## 2. Manifest v1

```json
{
  "schema_version": 1,
  "title": "영상 프로젝트 납품 검사",
  "expected_files": [
    {"path": "계약서.txt"},
    {"path": "deliverables/final.mp4", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
  ],
  "limits": {"max_files": 20000, "max_bytes": 8589934592}
}
```

Replace the example digest with the actual expected SHA256. Strict relative slash-separated paths only; no parent traversal, duplicate casing, colon, trailing spaces/dots, wildcard expansion or automatic NAS discovery. Every file in selected root is hashed read-only up to configured limits; additionally 25,000 directories max. A missing required file or mismatched hash blocks READY; unreadable, links, interrupted, changed directory or exceeded scan limits yield INCOMPLETE, and duplicate/version candidates yield NEEDS_REVIEW.

## 3. Legacy CLI, tests and report evidence

```bash
python -m flowpilot_universal --root ./authorized --manifest ./requirements.json --json ./new.json --html ./new.html
python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q flowpilot_universal
```

CLI report paths must be fresh and **outside** root. GUI creates unique JSON/HTML report pairs and SQLite audit database `.flowpilot-history.sqlite3` in the chosen output directory; old rows/old reports are preserved. The SQLite backup operation is user-triggered. No user files or report files are silently deleted. In case of a failed second report, a first partial artifact is retained for manual inspection (do not mistake for completed report).

## 4. Validation and limits

Code SHA `e6d4d450cf2014d985f9cf97be1d91d5ab4d63ec`, GitHub Actions [#43379604599](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43379604599): Linux30/30 and Windows30/30 tests PASS, compileall PASS. Tests use synthetic folders and headless GUI import only. Real desktop window interactions and customer Windows10/11/USB/SMB NAS are **NOT RUN**. Directory re-list is best-effort only; races, reparse/junction and immutable-snapshot claims are unverified. No EXE installer, PDF output, actual customer rights, legal license package or sale approval. True incremental resumption remains absent.

**Official final-design completion UNASSESSED**, not 70%. User goal of 70% remains in progress until whole locked blueprint F01–F10 owner-approved weighting and independent acceptance. Do not remove central [작업중] or RELEASE HOLD. See `BLUEPRINT.md` and `P70_EVIDENCE.md`.
