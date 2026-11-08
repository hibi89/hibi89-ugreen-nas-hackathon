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
