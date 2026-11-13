# FlowPilot Universal P85 exact evidence / deficiencies — 2026-11-13 KST

**Owner target:** final-design 85% of unchanged F01–F10; approved 100-point weighting and whole product customer acceptance are missing, so official final rate **UNASSESSED**, target 85% **NOT CERTIFIED**, central **[작업중]** retained, SALE RELEASE HOLD.

## Source and CI evidence
- Repo `hibi89/hibi89-ugreen-nas-hackathon@product/flowpilot-universal`; functional SHA `b66ba07b1cef34f0dff7683a9edc5e44684ac852`.
- [Final code CI #43383780676](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383780676): Ubuntu+Windows Python3.11 **55/55 unique tests PASS each, 0 FAIL, 0 SKIP**; portable 8 tests repeated (not extra unique) each; native Tk consent→scan→saved evidence verify→history→backup→rescan GUI **1 PASS each** (Linux Xvfb and Windows GitHub hosted); compileall PASS, 2/2 jobs SUCCESS.
- [Final-design policy CI #43383781197](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383781197) SUCCESS; it enforces evidence policy, not 85% product certification.
- This tests synthetic local files on CI. Windows runner is NOT a buyer Windows10/11; no physical USB/UNC SMB/NAS or customer data.

## Final-design requirement mapping
| ID | Implemented and verified | Missing for final acceptance |
|---|---|---|
| F01 consent/scope | Tk consent, path scope guards | real client/SMB authorization |
| F02 delivery templates | v1 manifest, duplicate JSON/Win unsafe path negative tests | commercial template designer/real examples |
| F03 integrity | fd-bound SHA256, bounded read, manifest original-byte audit | immutable snapshot/hostile race guarantee |
| F04 duplicate/version | deterministic content + filename candidate rules | real semantic conflict adjudication |
| F05 safety | read-only, link/reparse refusal, size+directory cap, race relist | real Win junction/SMB/ACL/volume acceptance |
| F06 evidence | create-only JSON/HTML/SQLite backup, report SHA/HTML byte parity check | native PDF, signed/authenticated provenance and retention policy |
| F07 customer UX/recovery | actual Tk widgets tested on both hosted OS, cancel/restart | full incremental resume and physical Win10/11 UX |
| F08 Windows delivery | deterministic `.pyz` archive/embedded hashes/Unicode CLI on Windows | standalone Windows EXE, installer, signing/SmartScreen/Defender and buyer no-Python |
| F09 hardware | synthetic OS temp file acceptance | physical Win10/11 PC/USB/authorized SMB NAS/multiple vendors |
| F10 commercial | explicit release HOLD and source conservation | owner-approved weights, licensing, support, customer sign-off |

## Design A/B and security limits
- A: third-party packager and signed self-contained Windows EXE. Better no-Python customer UX; requires legal component review, dependency execution/CI and signing and customer native tests. **Not implemented**, not silently waived.
- B: first-party Python standard-library zipapp `.pyz`, no additional paid software/APIs, reproducible source SHA + create-only sidecar. Implemented and tested. Python3.11+ is still required, and SHA **does not authenticate** a malicious actor who can replace artifact and checksum together.
- SQLite local report verifier compares JSON SHA to recorded `report_sha256`, compares status/counts and byte-for-byte HTML to JSON renderer. This detects non-coordinated tampering but **does not** cryptographically authenticate ledger or source provenance. No immutable source snapshot or full hostile Windows SMB TOCTOU proof.

## Failure and correction history
- [#43382503709](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43382503709): initial P85 package build failed UTF-8 filename due ASCII checksum sidecar (6 errors/OS); changed sidecar to UTF-8.
- [#43382697964](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43382697964): Windows 1 FAIL from cp1252 help output with Korean archive path; embedded bootstrap stdout/stderr UTF-8 fixed.
- [#43382812262](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43382812262) resolved; [#43383054430](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383054430) strict manifest/hash success; [#43383357720](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43383357720) Windows hosted Tk success; final #43383780676 ledger verification and GUI tests success.

## Rollback, outputs, release
- Pre-P85 branch HEAD `885f382e45246935aa9a34c840e5f5876fe57e1c` remains in Git history. Only isolated product branch modified; UGREEN contest lead/main/Skill, original submissions, customer files, paid credentials and hosted deployments unmodified.
- Report outputs and created SQLite backups are create-only, local; `.pyz` created in ephemeral CI tests but is **not uploaded or published** for download; no production URL/Vercel (N/A).
- Next: safe genuine incremental checkpoint, native EXE/license/signature only with owner-approved packaging choice, real Windows10/11/USB and consented SMB, customer PDF and legal ownership, F01–F10 100-point approved rubric. Until actual whole-design 85, central `[작업중]` remains and sale HOLD.
