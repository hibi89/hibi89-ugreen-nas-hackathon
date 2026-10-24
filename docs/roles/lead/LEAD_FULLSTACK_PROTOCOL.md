> **2026-10-24 KST · 현재 최우선 공시 / 한 문장 복원:** 사용자 명령 **`[유그 해커톤 깃헙 레포지토리 확인하고 작업하셈]`** → [START_HERE.md](START_HERE.md) 읽기 → 최신 `lead/ugreen` HEAD 및 [LEAD_ACTIVE_WORK](docs/roles/lead/LEAD_ACTIVE_WORK.md) 확인 → **총괄이 직접 작업**. 별도 작업자/구형 디스패치는 폐기. 본 문서 하단의 구형 설명은 이력이다.

# UGREEN — single lead / direct development protocol (CURRENT)
Effective 2026-10-24 KST. Precedence: participant decision > this current protocol > lead active work > historical dispatch notes.

- UGREEN lead is the ONLY active UGREEN AI chat: owns official SDK research, architecture, code/Skill authoring, tests, security review, ZIP/PDF and submission. No separate worker chat; user `ㄱ` means this lead takes next actual step immediately.
- Read `lead/ugreen` latest remote HEAD, `LEAD_ACTIVE_WORK.md`, `STATUS.md`, `HANDOFF.md`, official source/previous evidence. Prior three functional roles are design areas (missing deliverables, final-version conflicts, privacy/permission), not independent executors.
- New source and documentation default to **`lead/ugreen`**; main is stable release gate and three old `feature/*` refs historical evidence. Do not delete/force-push or replace any. Import reviewed feature artifacts selectively after actual diff/constraints assessment, not wholesale unsupervised merging.
- Old dispatcher `docs/dispatcher/CURRENT_TASK.md`, `BACKLOG.md`, `REVIEW_LOG.md`, `DISPATCH_PROTOCOL.md`, `docs/WORKER_START_HERE.md` are archival only. Even old READY/IN_PROGRESS does not authorize a new chat or code.
- One current lead task in `LEAD_ACTIVE_WORK.md`; execute as far as available tools/permissions allow, report CONFIRMED / UNVERIFIED / BLOCKED distinctly, avoid two identical failed approaches. Full SDK archive contents, exact supported CLI syntax, Expert Agent names, rights, version hashing, privacy checks and model locality must be proven by first-party source before writing allegedly runnable Skill CLI steps.
- Before edits: examine supported tools, permission, zero-cost API limits, data locality, file scope, recovery and validation. Read-only and no external PII transmission. Need explicit user approval for spending, public/privacy permissions, irreversible data changes, scope degradation. ZIP only recognized `SKILL.md` and directly linked Markdown references under official Round 1 rules.
- On meaningful implementation: run supportable synthetic/official-tool tests, identify omitted NAS runtime/CI, check source unchanged and reproducibility; commit lead STATUS/HANDOFF/TO_HACKATHON_LEAD and active work with SHA; verify remote and (if any) CI, and main only after validated integration.
- Deadline internal Nov 10 KST, official Nov 16 16:45 KST. Only actual Devpost receipt proves submission. GitHub activity is not product success.
## Choice
A chosen: direct lead development/verification on one `lead/ugreen` workline. B retired: rotate feature branches and 2-chat READY + manual acceptance. A removes handoff overhead while retaining the archived three branch refs, security and release gates.


## Resume and release evidence (binding)
- At every major milestone update `LEAD_ACTIVE_WORK.md` (single next action, date, blockers), `STATUS.md`, `HANDOFF.md`, `TO_HACKATHON_LEAD.md` together. Source and testing evidence first, then git commit and remote SHA verification; do not recursively embed the same pending commit SHA into itself. When code actually changes, test/review code + CI/Production scope separately. New chats start with [START_HERE](../../../START_HERE.md) even when user supplied only the short Korean phrase. No background work or automatic sync without user invocation.

## One-line new-chat restore and always-current handoff
- `[해커톤총괄 깃헙 레포지토리 확인하고 작업하셈]` → `lead/ugreen/CHAT_BOOTSTRAP.md` → current remote HEAD + `LEAD_ACTIVE_WORK.md` → next authorized investigation/code/testing. Do not launch archived dispatcher/worker.
- Major change/chat move requires STATUS/HANDOFF/TO_HACKATHON_LEAD and active-work synced with real evidence, commit/remote SHA checked; update stable bootstrap only if routes/roles change. No background sync or untested NAS completion claims.
