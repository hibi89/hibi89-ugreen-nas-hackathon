> **통합 수뇌부 전달 — 필독 (2026-10-24):** 사용자 요청으로 [상위 총괄 감독 의견](docs/FROM_HACKATHON_COMMAND.md)을 직접 수신했다. **새 채팅 복원·주요 작업 착수 전에 반드시 읽고**, 해당 지적을 `TO_HACKATHON_LEAD.md`에 수용/차단/근거 있는 반론/검증완료로 답신한다. 우선순위 지침은 정본 진척 JSON·최신 원격 소스·실 CI 결과의 수치를 덮어쓰지 않는다. 무단 제출/계정/비용 변경 없이 현행 총괄 직접 개발 체제 유지.

> **2026-10-24 최신 우선 규칙:** [MASTER_PROGRESS.md](MASTER_PROGRESS.md) = 날짜별 24건의 DONE/PARTIAL/BLOCKED/NOT_STARTED·선행 작업·테스트 증거·기본/별도 예비시간에 관한 **최신 진행 정본**. `lead/ugreen` 원격 HEAD 확인 후 이 문서를 **가장 먼저 읽고**, 이후 LIVE_HANDOFF/LIVE_STATE와 증거를 대조한다. **작업을 끝낼 때마다 MASTER를 포함한 필수 인수인계 파일을 같은 push로 갱신**하고 GitHub Actions 진행표 무결성 검사를 통과해야 한다. 아래 구형 읽기 순서는 MASTER 우선 원칙에 따라 해석한다.

# UGREEN — 한 문장 복원 (2026-10-24 KST 최신 규칙)

**사용자 명령(그대로 입력):** `[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]`

이 문장을 받은 새 ChatGPT 대화는 **UGREEN NAS AI Hackathon의 단일 총괄 겸 직접 개발자**로 복원한다. 긴 인수인계 프롬프트·채팅 기록·사용자 재설명은 요구하지 않는다. GitHub의 **`hibi89/hibi89-ugreen-nas-hackathon` 저장소 `lead/ugreen` 최신 원격 HEAD**가 작업 상태의 정본이며, `main`·옛 feature 브랜치·오래된 문서의 과거 상태를 현재 지시로 사용하지 않는다.

## 새 채팅 실행 순서 (추가 확인 질문 없이)
1. GitHub 연결 도구로 `lead/ugreen`의 **현재 원격 HEAD SHA**를 가져온다. 연결이 실패하면 접근 차단 사실만 설명하며 임의로 진행 상황을 만들지 않는다.
2. **반드시 이 순서로 최신 버전 읽기**: [`docs/roles/lead/LIVE_HANDOFF.md`](docs/roles/lead/LIVE_HANDOFF.md) → [`docs/roles/lead/LIVE_STATE.json`](docs/roles/lead/LIVE_STATE.json) → [`docs/roles/lead/LEAD_ACTIVE_WORK.md`](docs/roles/lead/LEAD_ACTIVE_WORK.md) → [`docs/roles/lead/DAILY_PROGRESS.md`](docs/roles/lead/DAILY_PROGRESS.md) 및 `DAILY_PROGRESS.json` → [`docs/roles/lead/CARRYOVER_TASK_SCHEDULE_20261024.md`](docs/roles/lead/CARRYOVER_TASK_SCHEDULE_20261024.md) → [`docs/WORK_ORDER_FLEX_POLICY_20261024.md`](docs/WORK_ORDER_FLEX_POLICY_20261024.md) → 해당 소스·테스트·CI 증거.
3. [`docs/roles/lead/SESSION_CLOSEOUT.md`](docs/roles/lead/SESSION_CLOSEOUT.md)의 **종료/인수인계 필수 절차**를 읽는다. 완료·미완료·차단·실측시간·예비시간 및 기존 선행 개발 중복 여부를 검증한다.
4. 사용자의 '작업하셈'은 **실제로 조사/구현/테스트/검수/원격 커밋**하라는 뜻. 단순 복원 보고서만 작성하지 않는다. 현재 READY하고 독립 검증 가능한 최우선 업무를 바로 수행하며, G1 SDK 차단은 해결됐다는 증거가 있을 때만 해제한다. G2/G3b/G3c/G4/G5의 이미 합성 검증된 코드는 재구현하지 않는다.
5. **작업이 끝날 때마다** LIVE_HANDOFF, LIVE_STATE, LEAD_ACTIVE_WORK, DAILY_PROGRESS(.md/.json), STATUS, HANDOFF, TO_HACKATHON_LEAD, WORK_TIME_LOG, 날짜별 이월표를 필요한 범위에서 모두 동기화하고 **같은 `lead/ugreen` 브랜치에 커밋/푸시**, 원격 SHA 및 CI 상태 재조회 후 종료 보고한다. 새 사용자 메시지 없이 백그라운드로 개발하는 기능은 아니다.

**2026-10-24 기준:** 해당 날짜에 수행한 실제 산출물 **100% 완료/남은 0h**(실제 경과시간 미측정), 오프라인 합성 CI [91/91 PASS](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40066651248). **G1 공식 SDK CLI/Expert Agent/권한/라이선스 내부 명세 및 NAS 실제 실행은 미검증·BLOCKED**. 다음 예정 G1 업무 **10/25 계획 1.5h+별도 예비 1.5h, 실제 완료 ETA 미정**. 전체 작품 제출/본선 진출로 혼동하지 않는다.

**대회 마감:** 예선 공식 2026-11-16 **16:45 KST**, 내부 조기 제출 11/10 조건부, 비용 신규 0원. 사용자 폴더의 외부 전송/삭제/유료 결제/공식 SDK에 없는 명령은 임의 수행하지 않는다.

## 정본/이력 우선순위
사용자 최신 지시 → **`lead/ugreen` 현재 원격 소스·테스트/CI** → `LIVE_HANDOFF.md` + `LIVE_STATE.json` → `LEAD_ACTIVE_WORK.md` → 날짜별 공시 → 과거 회의록/옛 UGR dispatcher·worker 문서. 구형 `[유그 ...]`·`[해커톤총괄 ...]`는 **과거 별칭이고 사용자에게 권장하지 않는다**.


**전체 24일 통합 체크표:** [MASTER_PROGRESS.md](MASTER_PROGRESS.md) / [JSON 정본](data/master_progress.json). 기존 LIVE_STATE·당일 DAILY_PROGRESS는 복원 및 상세 증거로 유지하고, 새로운 작업 매번 정본 JSON→MD 자동 생성→CI 검증을 추가한다.
