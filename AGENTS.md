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
