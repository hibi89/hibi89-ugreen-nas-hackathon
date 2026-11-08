## 2026-11-09 KST — G281 LOCAL SQLITE JUNCTION HARDENING AND PRE-NAS GATE REVIEW

- Scope: pre-NAS 100-point engineering rubric only; genuine-NAS-inclusive 73/100 stays unchanged. No owner-private ZIP/PDF bytes modified or published; Round1 Devpost remains submitted.
- Verified code: `tools/flowpilot_local_backend.py` commit `60d21695601651f780f276b18b60b53ee5aba852`, four new regression tests in `e460d78c257a72d48d1321feb6fbf4bb5b8e7c6b`. Existing SQLite DB path gate checked ordinary symlinks but not Windows reparse/junction flags; use G278's already adopted read-only `lstat` reparse helper on entry and all parent components at create and reconnect. Ordinary `O_EXCL` creation preserved. This is preflight, not TOCTOU-proof against concurrent root replacement.
- Actual CI on `e460d78c`: Linux **1731 PASS / 0 FAIL / 16 SKIP** (1747) and Windows full SUCCESS, [functional run 42515387285](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/42515387285); readiness [42515387331](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/42515387331), master [42515387314](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/42515387314), closeout [42515387312](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/42515387312) all SUCCESS (4/4).
- Real Chromium localhost HTTP+SQLite+CSV SHA/consent E2E source `60d21695` [run 42515358906](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/42515358906) SUCCESS. Only test file changed afterward, so browser-serving application code remains byte-identical at `e460d78c`. NAS/registered Expert/Docker production NOT_RUN.
- G280 **evidence assessment:** workflow 25/25 (prior fixture + current integration), security/recovery 20/20 (current regression and prior recovery tests), local UI/API 15/15 (real Chromium), Skill first-party exact-final Checker and entrant personal rights **0/20 pending explicit permission/attestation** (private final ZIP structural and digest checks previously PASS but not sufficient), final PDF+ZIP disclosure 10/10 (Library copies previously hashed; Devpost-upload byte identity still unknown and no claim made), Linux/Windows CI 5/5. Reproducible documentation gate **5/5 conditional on this documentation commit's closeout/master CI success**, otherwise HOLD. Thus **75/100 strictly confirmed before documentation CI, at most 80/100 after verified same-commit closeout**; never call 100% from source-only checks.
- Outstanding: separately authorize inspected official Uliya 0.7.3 read-only Checker on exact private final ZIP SHA256 `d1d362f1d88507a97e04ce2b186040786aa3a6ec13b4840b7d436a8e45c45984`; entrant personally determines work/IP/license/AI attribution rights. Keep original untouched. Genuine NAS runtime only if finalist, separate approval.
- Recovery: ordinary revert code commits `60d21695` and `e460d78c` if compatibility regression is verified; do not force push. This doc change alone does not modify production or run a vendor executable.

> **2026-11-09 VERIFIED:** `5fb9bb70` functional GitHub Actions 4/4 SUCCESS; Linux 1727 PASS / 0 FAIL / 16 SKIP, Windows full SUCCESS; this completes G280 ZIP guard regression but not the entire PRE-NAS 100%. First `39fc881e` synthetic fixture error was corrected.

# FlowPilot 3.0 — NAS-excluded 100% acceptance baseline (2026-11-09 KST)

**OWNER APPROVED:** Complete the full NAS-independent product by Nov 11, 2026; derive later contest submissions from the finished product rather than cutting features to fit a submission. Keep the already-submitted Round1 Devpost project unchanged unless independently authorized.

**Keep both score semantics:** historic whole-product score **73/100** from G242 remains unchanged, including 20 points native NAS and 5 points release/round-two. The NEW **pre-NAS engineering score** has its own 100-point denominator, no retroactive credit from renormalizing 73/100. Do not claim 100% without evidence against every row.

| Mandatory NAS-independent gate | Points | Acceptance evidence |
|---|---:|---|
| Natural-language goal → bounded typed workflow → result | 25 | Real owner-local synthetic fixture E2E, reproducible trace |
| Consent/security, missing/conflict and error recovery | 20 | Scoped read-only, symlink/junction, partial, timeout, replay tests |
| Local operator UI/API | 15 | Actual local HTTP and Chromium browser execution; not mocked UI |
| Exact final Skill ZIP & official contract | 20 | Five expected linked Markdown members; full CRC/UTF-8/permission checks; exact-first-party Checker exit0 on final bytes; owner's separate license/rights review |
| Exact PDF+ZIP and truthful release information | 10 | All ten answers <=500 English words, matching ZIP SHA, size/format and no fake live-NAS or uploaded-byte claims |
| Same-code Linux and Windows CI | 5 | Current source GitHub workflows passed, 0 unexplained FAIL, SKIP reported |
| Reproducible closeout and demo runbook | 5 | STATUS/HANDOFF, rollback, tested SHA and Nov11 freeze decision |
| **Full PRE-NAS completion** | **100** | **All conditions actually met** |

**Initial state — NOT 100%:** Existing functionality has prior G278 Linux 1722 PASS/0 FAIL/16 SKIP and Windows success, plus local browser history, not current-source CI. Exact current Library ZIP 18774B SHA256 d1d362f1d88507a97e04ce2b186040786aa3a6ec13b4840b7d436a8e45c45984 independently CRC-passed, five Markdown; final PDF 31346B SHA256 34ae9d7fecccac5bde10d977597b76f5fa7e43f3a6ecb737058314b4d8a17db7. Official Checker has **NOT run on those exact current final bytes**; entrant IP/rights approval remains personal; Devpost submitted event verified, uploaded binary equality unknown.

**Nov9:** eliminate a real local release-integrity flaw: old G274 checks only two text members and could accept corrupt or unreadable other references. New G280 checks every expected member and adds five negative tests. Verify exact-source CI before marking complete.
**Nov10:** run full local workflow/UI/security recovery and detect actual missing features, no redundant synthetic-only work.
**Nov11:** verify final immutable ZIP+PDF, official Checker only after separate explicit owner authorization, same-source CI, scope/risk review and freeze. If any gate fails, report NOT_READY and the exact evidence; never fake 100%.

**NAS excluded ≠ NAS verified:** registered Experts, signatures, effective permissions, completeness and data locality require finalist NAS access; Round2 real footage cannot be claimed or substituted. No vendor JS, 3h trial, external upload, license acceptance, payment, or repo disclosure is approved by generic 'ㄱ'. Original owner-private artifacts must not enter this public repo. Rollback via normal revert only.
