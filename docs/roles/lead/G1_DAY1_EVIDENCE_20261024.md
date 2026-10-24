# Day 1 — G1: official UGREEN creation tool access and offline fail-closed prototype
Date: **2026-10-24 KST** (advanced execution of scheduled 10/25 work), owner UGREEN lead, source branch `lead/ugreen`.

## Measured facts (not assumed success)
1. Official [UGREEN Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) §3 link #83 led to directly identified CDN object **`https://cdn.shopify.com/s/files/1/0630/9416/1602/files/uliya-skill-kit-0.7.3-en.zip?v=1790578898`**. Thus official **archive link basename shows 0.7.3-en**, not a validated manifest or verified internal SDK version.
2. Web archive click returned **HTTP 400 in browser-reading service because it cannot render application/zip**. This is **not** evidence the CDN object itself returns HTTP 400 to regular download clients.
3. **Materially different network path** attempted: direct CDN download with container download helper → download failed; separate raw Python urllib directly to CDN → `URLError [Errno -3] Temporary failure in name resolution`. This is tool sandbox egress/DNS restriction; **0 ZIP bytes downloaded**; ZIP SHA/contents/license/CLI commands/registered agent spec all **UNVERIFIED**.
4. Independent official [Uliya user guide](https://support.ugnas.com/detail/article/en-US/850) confirms existence of **File management assistant**, **Document assistant**, and **Skill management Tools**. Its File/Document/Learning dedicated chats require uploaded files before task submission; Smart Task can select assistants; a chat has local/hybrid/cloud model selection. **These are user-interface capabilities, NOT callable Skill CLI or registered Expert Agent command signatures.** Cloud model configuration may transmit documents: keep optional, consent and data safety gate.
5. Official hackathon [Rules](https://ugreenhackathon.devpost.com/rules) require registered expert-agent and supported CLI, forbid arbitrary executables/scripts in submissions. **Do not place this repository's prototype Python or tests in Round 1 ZIP.**

## Independent offline source & tests (distinct from official SDK)
- `src/projectready/readiness.py` = **pure deterministic** evaluation of supplied explicit relative paths + declared scan completeness + version/access/privacy independent gate states. `tests/test_readiness.py` tests safety boundaries; no SDK/NAS/file reading/network involved. `src/projectready/__init__.py` marker.
- In the local container a matching prototype/test harness was exercised with `python -m unittest discover -s tests -p 'test_readiness.py' -v`: **16/16 synthetic tests PASS**. Remote file revision should **also** run GitHub Actions on push; do not present CI success until a real run is confirmed.
- This pure reference engine **cannot prove** a real file exists, that a scan is complete, or that security/version checks were performed. Manually supplied PASS values in synthetic tests are mock inputs only. Production READY requires a validated official adapter supplying independent evidence; without that, leave `NOT_CHECKED`.
- Test cases: complete success, missing file, partial/denied/not-run, unverified gates, version review, privacy fail, case-sensitive mismatch, malformed paths, duplicate IDs, unknown gate/status, empty requirements and optional file.
- Installed official tool validator: **NOT RUN**. NAS actual runtime: **NOT RUN**. Registered Agent calls: **0**. Paid API: **0**. Additional spend: **0 KRW**.

## G1 gate and next action
**Day1 partial:** obtained exact official CDN artifact locator and product UI-specific constraints, plus independent tested fail-closed contract. **G1 remains BLOCKED**: official package archive and precise UGOS Skill creation tool syntax not available in this execution environment.

**Next single task:** On an authorized participant computer, privately download official ZIP from the Starter Kit §3 and inspect its `SKILL.md`, references, CLI/agent definitions, checker instructions, license and SHA256. Preserve binary privately; never publish potentially proprietary package to Public GitHub. If an authorized GitHub-connected environment cannot obtain it, request **official UGREEN support/community** for textual documentation of exact registered agent IDs, read/list CLI schemas and validator. No repeated sandbox DNS retry. Only then integrate an official adapter and approve G2 contract.

Source status: documentation PASS, local synthetic unit tests PASS (independent), network/download FAILED due tool environment, SDK/CLI/NAS validation NOT RUN. Planned day 10/25 effort **1.5h+1.5h** is a future budget, not verified actual elapsed time today. **Observed wall-clock duration not instrumented**; do not falsely convert prompt interactions to paid labor hours.


## GitHub remote CI evidence (independently checked AFTER commit)
- Source remote HEAD checked: `lead/ugreen@b97b23a302e6d7edc5c6013557e93c0b749ce8d0`.
- GitHub Actions workflow **Offline readiness contract**, push run **#40063814809**: **completed / success**. CI job ID `120782734697`, step `Execute synthetic offline tests only` **success**. Decoded job logs explicitly end `Ran 16 tests in 0.002s / OK`.
- Permalink: https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40063814809
- This verifies the **remote checked-in source**, superseding the earlier local-only 16 PASS evidence. STILL not official UGREEN Tool validator, actual registered Expert Agent, SDK ZIP, or NAS real-user test.
