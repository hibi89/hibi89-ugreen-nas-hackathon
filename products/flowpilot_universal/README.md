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
