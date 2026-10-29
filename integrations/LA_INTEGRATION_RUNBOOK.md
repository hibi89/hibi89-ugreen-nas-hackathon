# UGREEN ↔ Lightning Azent v0 integration

This branch stages a **UGREEN-side, read-only compatibility adapter**. It does not bundle HAE code or convert UGREEN's NAS Skill into a local workflow runner.

## Files
- `integrations/ecosystem_contract.py` — owner intent, scope, metadata consent and runtime permission gates
- `integrations/la_bridge.py` — LA `LAExecutor.preflight()` plan preview and `audit()` event/approval counts only
- `tests/test_la_bridge.py` — isolated fake-API contract tests (not live LA proof)
- `tools/verify_la_runtime_bridge.py` — opt-in smoke using an **owner-trusted local HAE checkout** and disposable synthetic SQLite files

## Local checks
From the UGREEN repository root:

```powershell
python -m unittest discover -s tests -p "test_la_bridge.py" -v
python -m unittest discover -s tests -p "test_ecosystem_contract.py" -v
python -m unittest discover -s tests -p "test_verify_la_runtime_bridge.py" -v
python tools/verify_la_runtime_bridge.py --la-package-root "C:\path\to\HAE\packages\lightning-azent"
```

The last command requires the owner to have independently checked out the actual LA package; no private code is fetched or copied by UGREEN. The optional smoke creates only disposable SQLite databases. It checks actual LA plan preflight and capability bounds, a literal read-only run, rejection of unapproved writes *before database creation*, one explicitly approved synthetic SQLite write, an approval-bound audit receipt without workflow values, independent SQLite row counting/integrity, and idempotent replay without duplicate business writes.
A passing **fake-LA smoke-harness test** proves this verifier detects rejected/duplicated writes; it is **not** evidence that the owner-installed private HAE LA package passed. A passing real-package smoke requires its own exact-source execution record. Runtime test PASS does **not** establish NAS access, Uliya Agent registration, document access, real customer safety, or external connector execution.

## Separation and release gates
- REA_APP is HAE's developer analysis workbench; **not** a runtime dependency.
- LA is a deterministic local engine; its current supported operations are not a NAS file-agent replacement.
- SOVIA has a **separately installed, opt-in, synthetic plan advisory adapter**; actual public SOVIA source passed the UGREEN CI review. DBVORA remains a separately owned, unconnected optional product. Neither grants NAS or workflow execution rights.
- UGREEN official Skill and original submission artifacts remain unchanged.
- Until live registered Uliya Experts, effective permissions, processing location, and owner authorization are verified: `NOT_CHECKED`, not `READY`.
- No customer information, credentials, access tokens, or private-source copies may be committed to this public repository.
- The overall day-ledger metric 14/24 covers planned milestones, **not product or official submission completion**.


## Evidence classification
- `LOCAL_FAKE_HARNESS_PASS`: UGREEN tests against an explicitly simulated LA API and temporary SQLite; protects the *test harness*, not real HAE compatibility.
- `HAE_LA_SYNTHETIC_PASS`: only after `verify_la_runtime_bridge.py` completes with the actual private HAE package installed by the owner. No NAS or Uliya Agent proof follows.
- `NAS_ULIYA_NOT_TESTED`: remains the correct status until authorized official runtime evidence is obtained.
- A previous private HAE Actions run #40906163642 failed with no runner and no executable steps; it must not be reported as a runtime test failure or PASS.

## Owner-local full chain (actual HAE LA + SOVIA, synthetic data only)

Use **three separate, trusted checkouts** of UGREEN, private HAE and public SOVIA. The script only imports from those checkout paths; it never copies private source or customer files into public UGREEN GitHub.

Required exact clean Git identities verified at authoring time:
- `HAE/feature/lightning-azent`: `9cba6424dadf3fadb0ccd6ed10040e322c4a62fa`
- `SOVIA_sovereign/develop`: `7418b23aff9b3abbd3faf5d1477e7244ec82b681`

From UGREEN source root, after the checkouts are available:

```powershell
python tools/verify_private_hae_chain.py --hae-root "C:\\path\\to\\HAE" --sovia-root "C:\\path\\to\\SOVIA_sovereign"
```

No special NAS credentials or network access are required. If the working code is dirty, a path does not exist, either checkout is at a different revision, or the imported packages fail the synthetic checks, the command exits nonzero and reports `FAIL` with a stable refusal code. **Do not change the expected SHAs or use `--force` to turn a failure into a pass.** To verify a newer HAE implementation, the changed package must be independently re-reviewed and the trusted commit pin explicitly updated.

Successful result requires **all**:
1. Genuine local HAE `LAExecutor`: pure preflight, temporary synthetic literal execution, refused write without database creation, explicitly approved SQLite write, metadata-only audit, one approval receipt, and idempotent replay without duplicate rows.
2. Actual SOVIA `assess`: zero finding for synthetic read-only plan, one write-approval finding for synthetic SQLite write plan.
3. FlowPilot: bounded goal preview and missing-input / declined-approval refusal; no user folder access.
4. Explicit `actual_nas_verified=false`, `registered_uliya_expert_invoked=false`, `release_gate=HOLD`.

The script reports SHA-256 hashes of installed LA runtime and SOVIA assessor entry files, pinned Git commit IDs, proof classification and non-sensitive counters. It does not echo source file paths, business values or owner-specific data.

An equivalent pinned-source **private HAE** workflow is in `hibi89/HAE` branch `verify/ugreen-la-bridge-20261030`; public GitHub Actions may not be used to retrieve private HAE source. The private HAE Actions runner failed before producing executable-step evidence; therefore private GitHub Actions is still **NOT_RUN** for this E2E. On 2026-10-30 the owner separately executed the exact pinned command on a fresh Windows local clone of all three repositories and supplied its complete JSON stdout with `result=PASS`. This is **owner-reported actual local code execution**, not an independently witnessed GitHub CI success or a live NAS test.

The sanitized transcript is at `integrations/evidence/owner_reported_local_e2e_20261030.json`. Its allowlisted consistency-checking logic is `integrations/local_proof_receipt.py` and the offline read-only verifier is `tools/verify_local_proof_receipt.py`. Run:

```powershell
python tools/verify_local_proof_receipt.py
```

Expected classification: `ACCEPTED_OWNER_REPORTED_SYNTHETIC_PROOF`; `independently_replayed_in_ugreen_ci=false`; `release_gate=HOLD`.

The owner-reported stdout contains the exact HAE SHA `9cba6424dadf3fadb0ccd6ed10040e322c4a62fa` and SOVIA SHA `7418b23aff9b3abbd3faf5d1477e7244ec82b681`, one approved synthetic SQLite row, one approval receipt, zero duplicate writes, four scenarios and a passing SOVIA advisory. It also explicitly records `actual_nas_verified=false`. No private source code or Windows paths were included in the public report. **The next external gate remains authorized official UGOS/Uliya NAS runtime evidence**, not another local synthetic LA proof.

## Continuous synthetic goal-to-SQLite path (owner-local exact-source PASS)

The earlier real pinned HAE/SOVIA report ran the actual LA database smoke and the FlowPilot/SOVIA preview as separate checks. The newer `integrations/goal_la_sovia_runtime.py` composes the *same synthetic write plan* through FlowPilot's bounded goal preview, real injected LA preflight, and actual SOVIA advisory, then — **only with a separate explicit synthetic-write approval** — executes that plan with LA and verifies its database write, approval audit and replay receipt integrity. This is a **fixed synthetic fixture for one supported goal**, not a general natural-language program compiler or NAS workflow engine.

From a trusted local UGREEN checkout beside separately pinned HAE and SOVIA checkouts:

```powershell
# Default: prepare and review; executor is never instantiated.
python tools/verify_connected_goal_runtime.py --hae-root ..\HAE --sovia-root ..\SOVIA

# Explicit disposable synthetic SQLite write plus idempotent replay.
python tools/verify_connected_goal_runtime.py --hae-root ..\HAE --sovia-root ..\SOVIA --approve-synthetic-write
```

The default must report `WAITING_EXPLICIT_SYNTHETIC_WRITE_APPROVAL` and zero executed writes. With explicit approval, a genuine pinned local HAE test can report `PASS` with one synthetic SQLite row, one approval receipt and zero replay duplicate rows. **Owner-local verification completed on 2026-10-30 KST:** The owner reported the output of the above exact command after a clean fast-forward update of the UGREEN integration branch to commit `f2fa9d48bcf655e431148f6b1583939879debbc6`, with HAE SHA `9cba6424dadf3fadb0ccd6ed10040e322c4a62fa` and SOVIA SHA `7418b23aff9b3abbd3faf5d1477e7244ec82b681`. The reported stdout states `status=PASS`, `la_execution_verified=true`, `sovia_advisory_reviewed=true`, `synthetic_write_rows=1`, `approval_receipts=1`, `replay_duplicate_writes=0`, and `ephemeral_sqlite_deleted_after_run=true`. The owner-provided, sanitized source of record is `integrations/evidence/owner_reported_connected_goal_e2e_20261030.json`. This is **owner-reported execution of genuine, Git-pinned HAE and SOVIA locally**, not independently replayed by public CI. Only a fixed synthetic goal fixture was tested; no NAS or Uliya Expert was called. Release gate remains `HOLD`.

Public CI uses a **fake LA executor**, the real UGREEN goal preview, actual pinned public SOVIA assessor and disposable synthetic SQLite, and tests missing approval, invalid goals, preflight failures, bad receipts and duplicate writes. This validates public integration behavior but does not import private HAE or touch NAS. The prior owner-reported real HAE/SOVIA PASS above remains a separate, narrower proof.

## Bounded multi-intent goal compilation — exact SHA approval

The new `integrations/bounded_goal_compiler.py` translates **one to three explicitly allowlisted** FlowPilot goal clauses into a valid `azent.ir.v0` synthetic LA plan, with an `intentN` literal and `storeN` disposable SQLite receipt per intent. Example labels are `CHECK_REQUIRED`, `HANDOFF_AUDIT` and `REVIEW_VERSIONS`. This is **not a general goal compiler**, does not inspect required files, and cannot delegate real Uliya file/document agents. All stored markers are `NOT_CHECKED`; no user prompts, file names or paths are present in LA runtime values.

A stable SHA-256 fingerprint covers the exact goal, required relative file scope, version-candidate mapping, allowed intents and compiled LA plan. This is a **consistency-bound operator approval**, not cryptographic identity verification. The first invocation must be a dry preview with **no LA execution or SQLite file creation**. A second invocation with the exact `approve_plan_sha256` enables **only synthetic, disposable** local SQLite writes and audit receipts; a changed goal/checklist/candidate mapping must be refused before writing.

With trusted HAE and SOVIA checkouts already available beside UGREEN, run a preview in PowerShell:

```powershell
py -3.11 tools\verify_bounded_goal_chain.py --hae-root ..\HAE --sovia-root ..\SOVIA --goal "파일 누락 확인 그리고 인계 확인" --required README.md
```

Read the returned `approve_plan_sha256` field and pass **that exact 64-character value** as `--approve-plan-sha256` while repeating all the same arguments. Do not substitute the separately returned `plan_sha256`: the approval hash additionally covers the user-supplied scope. Version comparisons require explicit `--candidate required=alternative` matching the approved `--required` path. All runs are isolated to temporary local SQLite under a disposable directory, and run receipts are redacted.

Public GitHub CI checks 15 negative/positive regression scenarios with a simulated LA runtime and also runs two distinct real UGREEN goal intents through the actual pinned **public SOVIA assessor**. No private HAE runtime is available in public CI. **Owner-local multi-intent E2E observed 2026-10-30 KST (user-provided PowerShell stdout):** After fast-forwarding UGREEN to `8de244114b4c2569c4f926d9ad289f11c3cddf53`, the owner ran the real-source local verifier with two allowlisted goals (`CHECK_REQUIRED`, `HANDOFF_AUDIT`). The first run reported `WAITING_PLAN_SHA256_APPROVAL` and zero SQLite writes. The owner then ran the exact same goal and scope with matching explicit approval SHA, producing `status=PASS`, two synthetic SQLite rows, one approval receipt, zero replay duplicates, SOVIA two advisory findings, and temporary database cleanup. Reported exact sources: HAE `9cba6424dadf3fadb0ccd6ed10040e322c4a62fa`, SOVIA `7418b23aff9b3abbd3faf5d1477e7244ec82b681`. The sanitized owner-supplied proof is `integrations/evidence/owner_reported_bounded_multi_intent_e2e_20261030.json`. This is real local LA/SOVIA synthetic execution **as reported by the owner**, not independent private HAE execution in public CI and not general natural-language execution. Vendor NAS/Uliya remain `NOT_TESTED`, submission/release `HOLD`. No official Skill/PDF/ZIP, access grant, timed trial or Devpost action was altered.

## Consented *actual local filesystem metadata* to synthetic LA/SOVIA receipts

The independent `integrations/local_metadata_la_chain.py` combines the existing bounded FlowPilot goal parser and exact-relative-path `lstat` inspector with the existing LA/SOVIA plan preview. Unlike the earlier entirely hardcoded `NOT_CHECKED` fixture, this path gets `PRESENT`, `MISSING`, `VERSION_REVIEW` or `NOT_CHECKED` from **local filesystem metadata**. It does not read file contents, enumerate owner directories or call the vendor NAS/Uliya Agents. **File names and filesystem metadata themselves may be personal/sensitive data**, so the local inspection requires its own explicit user consent and must be used only on owner-approved, trustworthy local paths. It is **NOT a network-drive/NAS inspector**, and a mounted remote drive cannot be presumed safe.

Approval flow:
1. Without `--approve-local-metadata`: bounded goal/scope preview only. No local root metadata access, no LA instance, no database.
2. With `--approve-local-metadata`: selected LOCAL file metadata `lstat` only, then real injected LA plan preflight and SOVIA advisory. No SQLite write; show `approve_plan_sha256` for exact path/goal/ordered observed states.
3. Separately provide that exact hash with `--approve-local-metadata --approve-plan-sha256 VALUE` to write **only redacted state counts, never filenames or contents**, to disposable LA SQLite; validate approval receipt, row count and idempotent replay. A changed state/order/scope invalidates the hash. This is a consistency hash, not an identity-authenticated signature or atomic filesystem snapshot.

Missing, symlink, unreadable or otherwise unverified local paths **block LA writes** rather than claiming `MISSING` without evidence. A version conflict can be recorded as `VERSION_REVIEW`, but no version is chosen or modified. Any return with `actual_nas_verified=false` and `release_gate=HOLD` must remain unpromoted. This is still development-only and outside the official submission Skill/ZIP.

Example using only a **new, disposable local folder** (do not point to an owner project, OneDrive working tree, mapped remote drive or customer records):

```powershell
# From the trusted local UGREEN checkout beside the exact pinned HAE/SOVIA clones
$fixture = Join-Path $env:TEMP ("ugreen-local-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $fixture | Out-Null
Set-Content -Path (Join-Path $fixture "README.md") -Value "synthetic fixture only"

# Preview only: no local path metadata read
py -3.11 tools\verify_local_metadata_la_chain.py --hae-root ..\HAE --sovia-root ..\SOVIA --root "$fixture" --goal "파일 누락 확인" --required README.md

# Explicitly consent to local-file metadata; returns an exact approval SHA
py -3.11 tools\verify_local_metadata_la_chain.py --hae-root ..\HAE --sovia-root ..\SOVIA --root "$fixture" --goal "파일 누락 확인" --required README.md --approve-local-metadata

# Optional second step: repeat the command and append
# --approve-plan-sha256 EXACT_APPROVE_PLAN_SHA256_FROM_PREVIEW
# Only disposable local LA SQLite is written, outside the selected fixture.
```

A safe fixture can also test `--required missing.txt` (blocked) or `--goal "버전 비교" --candidate README.md=README_final.md` with a separately created synthetic `README_final.md` (review needed). Exact-source HAE and SOVIA must still be verified on the owner's PC; **public CI has real OS synthetic lstat, simulated LA SQLite and real pinned public SOVIA, not private HAE or NAS**. This module makes no official NAS readiness or Devpost claim.

**Safety limitation:** the underlying local metadata inspector is not an atomic file snapshot; on an untrusted concurrently changing filesystem or Windows reparse points, only its conservative `NOT_CHECKED`/BLOCKED reporting is meaningful. Do not use it to claim production path security or privacy compliance.

## Six-scenario owner-local HAE/SOVIA matrix (single opt-in command)

The new `tools/verify_local_lstat_matrix.py` runs **six deterministic disposable-local cases** without any user-selected folder: unapproved preview, present file, missing file, conflicting version, stale approval after an observed state change and two-intent local metadata preflight. It constructs a fresh private temporary folder and non-sensitive synthetic files, calls the actual host OS's `lstat`, then invokes the pinned private HAE Lightning Azent and public SOVIA sources selected by the owner. It never uses an actual NAS or Uliya Agent, and never opens fixture file contents. Public CI uses fake LA plus the actual pinned public SOVIA assessor; **owner-local exact-H AE run is a separate gate**.

From the verified UGREEN checkout beside the trusted pinned HAE and SOVIA clones:

```powershell
# No SQLite execution; default previews 6 disposable synthetic cases
py -3.11 tools\verify_local_lstat_matrix.py --hae-root ..\HAE --sovia-root ..\SOVIA

# Explicit consent ONLY for temporary synthetic SQLite writes (2 intent rows)
py -3.11 tools\verify_local_lstat_matrix.py --hae-root ..\HAE --sovia-root ..\SOVIA --approve-synthetic-writes
```

The second command must report `result=PASS`, `scenario_count=6`, `synthetic_write_rows=2`, `approval_receipts=1`, `replay_duplicate_writes=0`, `actual_nas_verified=false`, `release_gate=HOLD`. A successful six-scenario result is not user-data readiness, cross-platform atomic path security, arbitrary goal execution, official Creator checker success, NAS permission evidence or a live registered Uliya file-agent invocation. The second command does not take any user folder path and creates only disposable local SQLite under its own temporary root.

**As authored, this matrix has not yet received an owner-local private HAE execution report.** Do not claim actual private HAE PASS from public CI. GitHub source receipts must remain scoped to synthetic testing; no credentials, machine paths or customer files belong in public evidence.
