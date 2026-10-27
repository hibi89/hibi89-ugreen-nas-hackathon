> **2026-10-27 G58 executable MVP sprint to Oct 28:** Owner separately accelerates HAE, Lightning Azent (LA), and REA_APP. UGREEN lead prioritizes one-command Python synthetic offline FlowPilot goal→plan→evidence demo; no frontend/deployment/NAS claim. [G58 MVP runbook](docs/submission/G58_RUNNABLE_SYNTHETIC_MVP_20261027.md). G58 new test/CI unverified until Actions; official Creator evidence + rights remain HOLD. Original source Skill and owner preview PDF/ZIP unchanged.

> **2026-10-27 LATEST USER CLARIFICATION — EXACT NAMED TOOLCHAIN LOCKED (UGREEN):** First read [concrete software/API/DB/model/deploy/QA tools](docs/architecture/FINAL_TOOLCHAIN_20261027.md). No extra features before initial submission; prior [submission freeze](SUBMISSION_SCOPE_FREEZE_20261027.md) still applies. This documentation does not prove functionality, model training, a deployed app, submitted entry or authorization for external payments/data.

> **2026-10-24 최신 우선 규칙:** [MASTER_PROGRESS.md](MASTER_PROGRESS.md) = 날짜별 24건의 DONE/PARTIAL/BLOCKED/NOT_STARTED·선행 작업·테스트 증거·기본/별도 예비시간에 관한 **최신 진행 정본**. `lead/ugreen` 원격 HEAD 확인 후 이 문서를 **가장 먼저 읽고**, 이후 LIVE_HANDOFF/LIVE_STATE와 증거를 대조한다. **작업을 끝낼 때마다 MASTER를 포함한 필수 인수인계 파일을 같은 push로 갱신**하고 GitHub Actions 진행표 무결성 검사를 통과해야 한다. 아래 구형 읽기 순서는 MASTER 우선 원칙에 따라 해석한다.

> **유그린 한 문장 자동 복원 — 최우선 규칙:** `[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]` → `hibi89/hibi89-ugreen-nas-hackathon`의 **`lead/ugreen` 최신 원격 HEAD** 조회 → [`LIVE_HANDOFF.md`](docs/roles/lead/LIVE_HANDOFF.md)·[`LIVE_STATE.json`](docs/roles/lead/LIVE_STATE.json) 읽기 → [`LEAD_ACTIVE_WORK.md`](docs/roles/lead/LEAD_ACTIVE_WORK.md) 및 [종료 시마다 필수 동기화](docs/roles/lead/SESSION_CLOSEOUT.md)를 준수하며 **다음 실제 작업을 곧바로 실행**. 역할·진행·일정·차단을 사용자에게 다시 묻지 않는다. `main`·옛 worker/dispatcher 문서가 충돌하면 이 최신 규칙과 원격 확인이 우선.

> **새 채팅 한 문장 진입:** `[해커톤총괄 깃헙 레포지토리 확인하고 작업하셈]` → [UGREEN CHAT_BOOTSTRAP.md](CHAT_BOOTSTRAP.md) (`lead/ugreen`). 원격 최신 HEAD 및 `LEAD_ACTIVE_WORK.md`로 실 작업 복원. 별도 작업자 채팅·구형 UGR 디스패치는 실행권 없음.

> **2026-10-24 KST · 현재 최우선 공시 / 한 문장 복원:** 사용자 명령 **`[유그 해커톤 깃헙 레포지토리 확인하고 작업하셈]`** → [START_HERE.md](START_HERE.md) 읽기 → 최신 `lead/ugreen` HEAD 및 [LEAD_ACTIVE_WORK](docs/roles/lead/LEAD_ACTIVE_WORK.md) 확인 → **총괄이 직접 작업**. 별도 작업자/구형 디스패치는 폐기. 본 문서 하단의 구형 설명은 이력이다.

> **현행 운영 방식(2026-10-24 KST): UGREEN 총괄이 직접 개발·테스트·검수까지 맡는다.** 별도 UGREEN 작업자 채팅/UGR READY 디스패치 **종료**. [LEAD_ACTIVE_WORK](docs/roles/lead/LEAD_ACTIVE_WORK.md) / [LEAD_FULLSTACK_PROTOCOL](docs/roles/lead/LEAD_FULLSTACK_PROTOCOL.md)에서 매번 다음 실작업을 확인. `lead/ugreen`에서 직접 작업, 기존 세 feature 브랜치는 원본·이력으로 보존. 아래 과거 채팅 분담 규칙은 폐기된 이력이다.

# UGREEN NAS AI Hackathon
> **3개 대회 전체 일정·충돌·제출 마감:** [docs/COMPETITION_SCHEDULE.md](docs/COMPETITION_SCHEDULE.md) (**2026-10-24 KST 공시**). 이 브랜치에서 작업을 시작할 때 마감과 내부 조기 제출 목표를 확인하며 공식 변경 시 대회 총괄에게 보고한다.


> 참가자는 **1명**, 개발 역할은 독립된 AI 채팅방 4개(대회 총괄 1 + 기능 담당 3). **2026-10-24 KST 초기 구조**. 이 저장소는 사용자가 생성한 **Public** 저장소다.

- 대회 목표(잠정): **NAS 프로젝트 파일 관리 AI Skill (잠정)**. 주제와 기능 범위는 사용자 승인 전 확정하지 않는다.
- 제출 마감: **2026-11-16 16:45 KST**.
- 전체 일정·상위 보고: [2026 통합 해커톤 상황실](https://github.com/hibi89/hackathon-command-center-2026/blob/main/START_HERE.md).
- 초기 단계: **브랜치·운영 문서 준비**, 코드·실 API·제품·제출물 구현은 미착수.

## 역할 브랜치
- `main`: 검증된 코드·최종 통합 기준.
- `lead/ugreen`: 대회 총괄, 설계/검수/기획/제출/상위 보고.
- `feature/missing-files`: 기능 개발 담당 1.
- `feature/version-conflicts`: 기능 개발 담당 2.
- `feature/privacy`: 기능 개발 담당 3.

## 읽을 문서
새 AI 담당자는 자기 **브랜치**에서 `HANDOFF.md` → `STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → 역할별 `docs/roles/<role>/OPERATIONS.md`를 읽는다. 역할별 문서가 다른 브랜치에도 있다고 가정하지 않는다.

- [공통 규칙](AGENTS.md)
- [요구 사항](REQUIREMENTS.md)
- [진행 현황](STATUS.md)
- [브랜치 운영](docs/BRANCH_WORKFLOW.md)

**중요:** 어떤 비밀값·고객 개인정보도 공개 저장소에 저장하지 않는다. 개발·범위·권한·비용 확장은 사전 승인 대상이다.

## UGREEN 총괄의 독립 실행 계획 (2026-10-24)
[ProjectReady NAS — 일정·역할·검수·0원 비용 계획](docs/UGREEN_EXECUTION_PLAN_20261024.md) (lead/ugreen 브랜치). 내부 조기 제출 11/10, 공식 예선 11/16 16:45 KST.


## Final ProjectReady schedule (2026-10-24 KST)
- [Approved UGREEN-only execution plan](docs/UGREEN_EXECUTION_PLAN_20261024.md)
- [3 worker assignments and acceptance criteria](docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md)
- Early final submission target **2026-11-10 KST**; official **2026-11-16 16:45 KST**.
- User-approved evidence-based client delivery Go/No-Go Skill, not three separate submissions. Product and NAS/CLI operation unverified; no new paid tools.


## [최신 운영] 하나의 UGREEN 작업자 채팅
- **UGREEN 총괄 채팅 + 공통 작업자 채팅 = 2개 채팅**. 이전의 작업자별 별도 대화 3개는 필요하지 않음.
- 공통 담당자 시작: [WORKER_START_HERE](docs/WORKER_START_HERE.md) → 매번 [CURRENT_TASK](docs/dispatcher/CURRENT_TASK.md)를 읽고 지정된 feature 브랜치에서 실제 작업.
- 총괄은 [BACKLOG](docs/dispatcher/BACKLOG.md)와 [DISPATCH_PROTOCOL](docs/roles/lead/DISPATCH_PROTOCOL.md)을 따라 각 단계 검수 후 다음 업무를 게시. 작업자 채팅은 그대로 재사용.
- 현재 READY UGR-001 공식 Skill Kit 조사, 대상 feature/missing-files. 다른 두 작업은 대기. 실제 작업자 실행/SDK 검증/Skill 구현은 아직 미확인.
- 내부 조기 제출 11/10 KST; 공식 예선 11/16 16:45 KST; 신규 현금 지출 0원 목표.
