> **2026-10-28 해총 최종 공통 개발·검증 지시 / 소유자 최신 결정:** [전 프로젝트 공식 운영 정본](https://github.com/hibi89/hackathon-command-center-2026/blob/main/docs/DEV_ACCELERATION_AND_VERIFICATION_20261028.md). **활성 슬롯=KIC(+DL), PayPal, UGREEN, LA 총 4개**, 일반 구현·검증은 GPT-6 **Instant**, 최초 설계/복잡한 고위험 문제·해총 독립 감독만 높은 추론. 기능 목표→구현+집중 테스트→실패 수정→기능 단위 커밋→필요 통합 CI→최소 문서. GitHub 파일별 호출·HEAD 반복·STATUS/HANDOFF 중복·동일 CI 반복 금지. 사용자 로컬 전용 검증은 안전한 한 명령 스크립트/로컬 Codex에 맡기고 **실제 실행 SHA/PASS·FAIL·SKIP**로 보고. `TO_HAECHONG.md` 재작성은 큰 개선이 있을 때만. 기존 설계·비공개 정보·외부 승인·보안·복구/대회 게이트 보존.
>
> **UGREEN 활성 슬롯:** Instant 기능 1개씩 구현하되 등록 Expert/실제 NAS 3시간 체험권 사용·외부 업로드·공식 제출은 소유자 별도 승인 전 금지. 합성 오프라인 PASS와 실제 NAS 완료를 구별하고 공식 Skill 정본·제출물 바이트를 보호.

> **2026-10-28 소유자 최상위 개발 가속 지시 (기존 중복 문서/테스트 의무에 우선):** 최초 설계 유지, 실제 기능을 1순위로 한다. 루프: 완료 조건→소스/테스트 기능 단위 일괄 수정→변경 기능 핵심 검증→결함 수정→한 번의 커밋→통합 회귀 확인→의미 있는 경우에만 STATUS/HANDOFF 최소 갱신. 기능·검증·차단 상태가 바뀌지 않은 사소한 수정마다 모든 live 상태 파일의 동시 갱신을 강제하지 않는다. `data/master_progress.json`을 변경할 때는 반드시 `MASTER_PROGRESS.md`를 함께 갱신한다. **정본 Skill `skill/flowpilot-nas/SKILL.md`을 변경하는 중요한 릴리스 범위에서는 STATUS.md와 HANDOFF.md를 모두 갱신**하고 공식 독립 Checker를 최종 바이트로 다시 실행한다. Windows에서는 `powershell -ExecutionPolicy Bypass -File .\verify_local.ps1 -Mode smoke` 또는 `-Mode full` 단일 진입점을 사용한다. AI 환경에서 실행 가능한 테스트는 AI/CI가 직접 처리하며, NAS·Agent·권한·개인정보·체험권·Devpost는 사용자 별도 승인 없이 호출하지 않는다. Release HOLD와 원본 보존·보안 테스트 의무는 완화하지 않는다. 테스트 수·문서량으로 제품 완성률을 계산하지 않는다. 다른 총괄 브랜치 임의 병합·강제 푸시 금지. 시간 미계측은 NOT_MEASURED, 추정은 추정으로만 보고한다. 이 단락과 기능 단위 CI가 본 문서의 과거 '모든 source/test push 10개 파일 갱신'보다 우선한다.

> **2026-10-25 조직 고정 — 해총/스총:** 해총은 [해커톤 상황실](https://github.com/hibi89/hackathon-command-center-2026) 통합감독, 스총은 Private SMAX² 제품총괄. 이 저장소 실개발은 기존 **UGREEN `lead/ugreen` 총괄**이 담당. [역할·최신 우선순위](docs/HAECHONG_STECHONG_ROLE_BOUNDARY_20261025.md)를 참고. 기존 한 줄 복원명령은 변경하지 않음.

> **2026-10-24 최신 우선 규칙:** [MASTER_PROGRESS.md](MASTER_PROGRESS.md) = 날짜별 24건의 DONE/PARTIAL/BLOCKED/NOT_STARTED·선행 작업·테스트 증거·기본/별도 예비시간에 관한 **최신 진행 정본**. `lead/ugreen` 원격 HEAD 확인 후 이 문서를 **가장 먼저 읽고**, 이후 LIVE_HANDOFF/LIVE_STATE와 증거를 대조한다. **작업을 끝낼 때마다 MASTER를 포함한 필수 인수인계 파일을 같은 push로 갱신**하고 GitHub Actions 진행표 무결성 검사를 통과해야 한다. 아래 구형 읽기 순서는 MASTER 우선 원칙에 따라 해석한다.

> **유그린 한 문장 자동 복원 — 최우선 규칙:** `[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]` → `hibi89/hibi89-ugreen-nas-hackathon`의 **`lead/ugreen` 최신 원격 HEAD** 조회 → [`LIVE_HANDOFF.md`](docs/roles/lead/LIVE_HANDOFF.md)·[`LIVE_STATE.json`](docs/roles/lead/LIVE_STATE.json) 읽기 → [`LEAD_ACTIVE_WORK.md`](docs/roles/lead/LEAD_ACTIVE_WORK.md) 및 [종료 시마다 필수 동기화](docs/roles/lead/SESSION_CLOSEOUT.md)를 준수하며 **다음 실제 작업을 곧바로 실행**. 역할·진행·일정·차단을 사용자에게 다시 묻지 않는다. `main`·옛 worker/dispatcher 문서가 충돌하면 이 최신 규칙과 원격 확인이 우선.

> **새 채팅 한 문장 진입:** `[해커톤총괄 깃헙 레포지토리 확인하고 작업하셈]` → [UGREEN CHAT_BOOTSTRAP.md](CHAT_BOOTSTRAP.md) (`lead/ugreen`). 원격 최신 HEAD 및 `LEAD_ACTIVE_WORK.md`로 실 작업 복원. 별도 작업자 채팅·구형 UGR 디스패치는 실행권 없음.

> **2026-10-24 KST · 현재 최우선 공시 / 한 문장 복원:** 사용자 명령 **`[유그 해커톤 깃헙 레포지토리 확인하고 작업하셈]`** → [START_HERE.md](START_HERE.md) 읽기 → 최신 `lead/ugreen` HEAD 및 [LEAD_ACTIVE_WORK](docs/roles/lead/LEAD_ACTIVE_WORK.md) 확인 → **총괄이 직접 작업**. 별도 작업자/구형 디스패치는 폐기. 본 문서 하단의 구형 설명은 이력이다.

> **현행 운영 방식(2026-10-24 KST): UGREEN 총괄이 직접 개발·테스트·검수까지 맡는다.** 별도 UGREEN 작업자 채팅/UGR READY 디스패치 **종료**. [LEAD_ACTIVE_WORK](docs/roles/lead/LEAD_ACTIVE_WORK.md) / [LEAD_FULLSTACK_PROTOCOL](docs/roles/lead/LEAD_FULLSTACK_PROTOCOL.md)에서 매번 다음 실작업을 확인. `lead/ugreen`에서 직접 작업, 기존 세 feature 브랜치는 원본·이력으로 보존. 아래 과거 채팅 분담 규칙은 폐기된 이력이다.

# UGREEN AI 역할 및 공통 운영 규칙

- 실제 참가자: 사용자 **1명**. AI 담당자들은 각자 독립 대화와 GitHub 브랜치에서 작업한다.
- 대회 총괄(`lead/ugreen`)이 제출·아키텍처·검수·통합·개발 지시 책임을 진다. 기능 담당자는 `feature/missing-files`, `feature/version-conflicts`, `feature/privacy`만 수정한다. 최상위 해커톤 총괄은 전체 일정·위험·공식 성과만 감독한다.
- 다른 브랜치의 소스/메시지/기능은 사용자 승인 없이 수정하지 않는다. `main`은 검증된 통합 기준이다.
- 시작: **자기 브랜치** `HANDOFF.md` → `STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → 역할별 `docs/roles/<role>/OPERATIONS.md`. 최신 GitHub HEAD·실제 소스와 대조한다.
- 작업 종료: 기능/실행/테스트/실패·검증·미검증 구분 → `STATUS`·`HANDOFF`와 메시지함/상위 보고 갱신 → 자기 브랜치에 커밋, 원격 SHA 검증. 단순 질의에는 불필요한 커밋 금지.
- 총괄은 새로운 기능 지시 전에 세 기능 브랜치의 최신 `TO_UGREEN_LEAD.md`를 전수 확인하고 `MESSAGE_REVIEW.md`에 기록한다. 채팅 간 자동 전송·실시간 동기화 없음.
- 원본·기존 정상 기능·데이터 보존. 설계 2안 비교 후 사용자 승인. 유료 API/결제·개인정보 외부 전송·권한/공개 설정 변경·기존 원본 변경은 승인 필요.
- 토큰·.env·비밀번호·개인정보·비공개 원본 업로드 금지(**저장소 Public**). API Sandbox 성공/합성 테스트/CI/Production 실제 동작을 구분한다.
- 이 운영 문서는 코드 개발 완성의 근거가 아니다. 대회 공식 규정은 https://ugreenhackathon.devpost.com/rules.


## [2026-10-24 최신 우선규정] 단일 공통 실행 담당자
- 과거 기능별 AI 채팅방 3개 가정 폐기. **UGREEN은 총괄 채팅 1개 + 하나의 공통 작업자 채팅 1개**. 같은 담당자 채팅이 최신 업무에 맞춰 feature 브랜치를 변경한다.
- 실행 전 lead/ugreen의 [CURRENT_TASK](docs/dispatcher/CURRENT_TASK.md) 최신 TASK_ID/STATUS/TARGET_BRANCH를 조회한다. **하나의 READY만 실행**, BACKLOG 임의 착수 금지.
- 작업자는 지정 feature 브랜치만 수정하고 그 브랜치의 TO_UGREEN_LEAD에 Task ID, DONE_FOR_REVIEW/BLOCKED, 증거/검증/원격 SHA 보고. 총괄 승인 후에만 새 READY로 전환한다. 리드/main 브랜치는 총괄 관리.
- [공통 작업자 시작 안내](docs/WORKER_START_HERE.md) 참조. 이 최신 규정이 위의 과거 '각자 독립 대화'보다 우선. 채팅 간 자동 알림/실행은 없다.
