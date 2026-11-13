> **최신 P85 추가개발 증거 — 2026-11-13 KST:** 기능/GUI 테스트 SHA `a96e727ba89bb87a4914e85c31da0898ce41c45d`, [Linux·Windows 회귀 https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387548967](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387548967) **각 63개 고유 테스트 PASS + 포터블 8개 재검사 PASS + Tk GUI 위젯 시나리오 2개 PASS**, 2/2 jobs SUCCESS; [정책 https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387549226](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387549226) SUCCESS. 취소 후 체크포인트 재사용은 완료 바이트를 재해시하지 않으므로 **NEEDS_REVIEW**, 캐시 제외 전체 검사에서만 READY. 별도 [Windows EXE 빌드·자체실행 https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387249760](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43387249760) PyInstaller 6.22.3 `--onedir --windowed` 생성·실제 EXE 자체검사 종료 코드 **0**, SHA256 `FEA326B7C73E104F08DDB9EAC13FDA0D09DFD2E785624973E3905A1E2559102E`. **unsigned / 미출시 / CI 임시 생성**. 고객 Win10/11 실기기, USB·권한 SMB, 서명/설치·PDF·인수·권리·승인 100점 가중치는 미완료. **공식 최종설계 85% 미인정(`UNASSESSED`), [작업중]·RELEASE HOLD 유지.**
> **2026-11-13 KST P85 개발 증거:** functional SHA `b66ba07b1cef34f0dff7683a9edc5e44684ac852`; [Linux/Windows CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383780676) 각 **55개 고유 테스트 PASS**, portable 8개 재실행/OS PASS, 실제 Tk GUI 1건/OS PASS; 2/2 jobs SUCCESS, 컴파일 검증 PASS. [최종설계 정책 검사](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383781197) SUCCESS. **기술 P85 일부 구현**이나 EXE/설치·실 고객 Windows10/11·USB·SMB NAS·진정한 증분 재개·PDF·상업권·승인된 전체 100점 가중치 미충족. 따라서 **공식 최종완성률 UNASSESSED**, 사용자 목표 85% 미인정, **[작업중]·RELEASE HOLD 유지**. [P85 상세](P85_EVIDENCE.md).
# FlowPilot Universal final-product design and P50/P70/P85 traceability

Source: central approved product brief at hackathon-command-center-2026/kmong-productization/docs/commercial/KMONG_3_NEW_PRODUCTS_20261112.md. This separate product MUST NOT be conflated with the UGREEN NAS Skill or its contest progress.

## Competing designs and choice
A. Depend on UGREEN Uliya Expert/Skill: potentially faster NAS integration but cannot promise other NAS/Windows compatibility, requires NAS/Expert authorization, creates dependency on a competition-specific runtime and unknown licensing. Hardware access and customer suitability remain untested.
B. Independent Python 3.11 local scanner of operator-authorized PC/USB/OS-mounted SMB path: no third-party runtime/API, no monthly hosting, portable contract and lower security exposure, but GUI/installer/real UNC SMB validation cost remains. **B selected for P50** (matches central brief). No automated NAS operation and no silent discovery.

## Final intended product and traceability (no retroactive percentage grant)

| ID | Final customer requirement | P50 implementation | Evidence / remaining acceptance |
| --- | --- | --- | --- |
| F01 | Explicit consent and scoped local/SMB source | Root CLI argument and regular directory preflight | Source engine.py; real SMB/permissions NOT_RUN |
| F02 | Template-based required delivery file matching | Schema v1 requirements manifest with strict relative paths | tests missing, traversal, collision PASS; GUI template library NOT_BUILT |
| F03 | Byte-level SHA-256 integrity check | fd-bound hashing with best-effort before/after metadata check | tests ready/mismatch PASS; cross-device race/immutable snapshots NOT_PROVEN |
| F04 | Duplicate/version conflict review | Exact-content duplicates, filename version candidates | tests duplicate/version PASS; semantic versions/collaboration NOT_BUILT |
| F05 | Source safe/no unauthorized mutations | read-only filesystem operations; links/reparse/special entries -> INCOMPLETE; file/byte/directory caps and directory re-list checks | synthetic Linux/Windows CI; Windows junction/directory TOCTOU hardening and real SMB NOT_DONE |
| F06 | Delivery evidence | Local create-only JSON + escaped HTML, consented SQLite history + create-only online SQLite backups, no network | synthetic CI and DB readback PASS; customer PDF, privacy/retention policy and real audit workflows NOT_DONE |
| F07 | General user workflow and error recovery | Tkinter GUI/explicit consent/progress; metadata-checked SQLite checkpoint per-file resume for provisional review; cancel->INCOMPLETE, reused cache->NEEDS_REVIEW, full no-cache rehash->READY | Linux/Windows 63 unit+2 Tk flows each in synthetic CI PASS. No cryptographically authenticated checkpoint, actual buyer Win10/11 UX or true trusted READY from reused hashes. |
| F08 | Production Windows portable delivery | Deterministic Python `.pyz`; PyInstaller 6.22.3 onedir unsigned Windows GUI `.exe` CI candidate with runtime smoke exit 0 and binary SHA logged | Offline folder candidate NOT published, no code signing/installer, physical buyer Win10/11/SmartScreen/Defender NOT_RUN; separate third-party licensing review required. |
| F09 | Authorized actual PC/USB/SMB hardware acceptance | No physical hardware touched | real Windows UNC share, NAS models and high-volume test NOT_RUN |
| F10 | Commercial user acceptance and legal delivery | no sale and no permission external transfer | EULA, copyright/3rd-party reviews, support, customer pilots, seller GO NOT_DONE |

**P50 engineering gate (internal, scoped):** F01-F06 have proof at synthetic Linux and Windows Python3.11 tests. This is NOT official 50% of final blueprint. The official completion percentage is **UNASSESSED** under OWNER-FINAL-BLUEPRINT-100, because a complete 100-point owner-approved item weight table and real end-to-end acceptance evidence have not been approved. Do not convert number of tests, internal stage names, or code lines to final percentage.

## Planned stage gates (not retroactive credits)
- P50: contract, independent offline core, fail-closed output, focused deterministic tests (implemented, synthetic only).
- P70: user GUI, guarded local report history/backup, bounded interruption and scan stabilization; true checkpoint resume remains OPEN. Synthetic technical coverage is substantial but full P70 acceptance is **PARTIAL**.
- P85: Windows EXE installer/portable signature, full negative security regression and user documentation.
- P95: real Windows10/11 local USB+permissioned SMB NAS from multiple vendors, independently checked report parity, business customer use cases.
- P100: verified consent/rights/contract, complete final blueprint owner-approved scoring, support/refund/license and real user acceptance, explicit commercial release GO.

Nothing here authorizes remote SMB credentials, external uploads, NAS scripts, paid subscriptions, production deployment or customer data access. Customer filenames in HTML/JSON are sensitive; output stays local only.

## P70 implementation snapshot (2026-11-13 KST)
- Implementation evidence: `product/flowpilot-universal@e6d4d450cf2014d985f9cf97be1d91d5ab4d63ec`; Actions [#43379604599](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43379604599) Linux30/30 + Windows30/30 PASS, compileall both. Final-blueprint policy gate [#43379605082](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43379605082) SUCCESS (policy only).
- Desktop GUI: `python -m flowpilot_universal.gui` selects root, manifest, separate output and requires explicit checkbox approval. Real interactive customer GUI NOT_RUN.
- Workflow: SQLite `.flowpilot-history.sqlite3` in selected output folder, create-only JSON/HTML with unique IDs, offline list and explicitly requested create-only SQLite online backup. A cancelled run records `INCOMPLETE` evidence and next scan rehashes all files; **not incremental checkpoint resumption**.
- Safer scans: directory names re-list and platform metadata check; file/byte limits and 25,000 directory hard cap; best-effort only, never immutable snapshot guarantee, no authorized physical SMB/USB evidence.
- **Official final-design completion is UNASSESSED.** OWNER-FINAL-BLUEPRINT-100 weights/independent acceptance are unapproved, so neither '70%' nor '50%' is an official completed product rate. Central [작업중] stays until actual user target achieved; RELEASE HOLD.
