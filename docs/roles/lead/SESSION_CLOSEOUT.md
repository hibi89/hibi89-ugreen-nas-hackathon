> **2026-10-26 G35 actual-artifact audit:** G34 PDF 1-page rendered at 200dpi and *visually inspected PASS*: 10 QAs, four disclosures, no clipping, 19 in-bounds text blocks, exact SHA `ba0fdf853386073df9cecd9bc88152d3188eaa3bbaf8886ac92ad1dace638991`; G32 byte-identical ZIP SHA `2b4260e3e27c6efde1d7857e9b80ab4441177b84a3cdf80544dcdb107933c077`. **Release HOLD**: exact G32 vendor static-pass still valid but two inert `delegate` syntax examples create potential UGREEN SkillHub Standards Article2.5 publication issue; new G36 candidate and new exact-SHA check needed. Entrant ownership, vendor license, approval, Devpost, real NAS unresolved. [Evidence](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead%2Fugreen/docs/submission/G35_G34_VISUAL_AND_RIGHTS_REVIEW_20261026.md). Ledger 2 DONE/12 PARTIAL/3 BLOCKED/7 NOT_STARTED; Oct26 G1 0% BLOCKED, 1.5h base and 1.5h separate reserve, real elapsed hours NOT_MEASURED.

> **우선 규칙 / MASTER:** 작업 종료 때마다 루트 [MASTER_PROGRESS.md](../../../MASTER_PROGRESS.md)부터 당일/선행 작업에 해당하는 원래 계획일 행을 갱신한다. 모든 push에 MASTER 파일 변경이 없으면 GitHub Actions 실패한다. 코드·테스트 변경 시 원래 9개 인수인계 파일 동시 변경도 유지. `python tools/check_master_progress.py`와 회귀 테스트로 원본 날짜·시간·증거 체크. 당일 100%와 전체 진도·공식 NAS 검증 절대 혼동 금지.

# UGREEN — EVERY WORK SESSION CLOSEOUT (필수, 새 채팅 자동 복원용)

**사용자 확정 단일 진입 문구:** `[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]`.

## 사용자가 작업을 호출하면
- 먼저 `lead/ugreen` **GitHub 최신 원격 HEAD**, `START_HERE.md`, `LIVE_HANDOFF.md`, `LIVE_STATE.json`, `LEAD_ACTIVE_WORK.md`, `DAILY_PROGRESS.md/json`, `CARRYOVER_TASK_SCHEDULE_20261024.md`, `WORK_ORDER_FLEX_POLICY_20261024.md`, 해당 코드/테스트를 실제로 읽는다. 다른 대회 브랜치를 혼동하거나 과거 작업자 지침을 복원하지 않는다.
- 사용자의 `ㄱ`/한 문장은 **작업 개시 허가**이다. 독립적으로 확인 가능한 G2~G5 선행은 가능. 과거 이미 구현한 코드는 중복으로 작성하지 않는다. 등록 Agent/CLI/NAS/PII는 검증되지 않은 상태면 명시적으로 `BLOCKED`/`NOT_CHECKED`.

## 각 작업 종료 전 반드시 (매번, 최종 답변 전에)
1. 구현·검증·실패 원인과 **증거/반례/미검증**을 구별한다. 합성 테스트 횟수는 실제 NAS 실행횟수가 아니다. 실제 사용시간 **미측정이면 null/미측정**; 시간이 없는데 추정으로 채우지 않는다.
2. 날짜(KST), 당일 약속한 작업 분모 **100%**, 완료 XX%/미완료 YY%, **남은 기본시간과 별도 예비시간**, 차단·외부 의존/실제 완료 ETA 미정 여부를 `DAILY_PROGRESS.md`와 `DAILY_PROGRESS.json`에 갱신한다. **10/24 100%와 10/25 G1 차단을 섞지 않는다**. 선행 업무는 실제 실행일과 원래 배당 날짜를 모두 기록한다.
3. 다음 작업 1개, 상태(READY/BLOCKED), 명확한 범위와 **허용/금지**, 완료 기준, 재시도 방지, 공식 테스트 불가할 때 대안을 `LEAD_ACTIVE_WORK.md` 및 `LIVE_STATE.json`·`LIVE_HANDOFF.md`의 맨 위에 반영한다.
4. `STATUS.md`, `HANDOFF.md`, `TO_HACKATHON_LEAD.md`, `WORK_TIME_LOG.md`, 날짜별 `CARRYOVER_TASK_SCHEDULE_20261024.md`를 **이번 작업 기준으로 최신화**한다. 새 코드만 만들고 인수인계를 빠뜨리지 않는다. 출시/Devpost/본선은 증거 없으면 미완료.
5. **실제 소스/테스트 변경**이 있으면 `python -m unittest discover -s tests -p 'test_*.py' -v`와 GitHub Actions 확인. 새 증거를 기록하고 `lead/ugreen` 브랜치에 커밋·푸시; 최종 **원격 HEAD SHA와 테스트 run ID** 다시 조회한다. 코드 커밋 SHA와 종료 문서 SHA가 다를 수 있음을 구분하고, 문서 안에 **자기 자신의 HEAD SHA를 미리 예언하지 않는다**.
6. 사용자 최종 응답은 작업 내용, 커밋 링크, 테스트, **오늘 XX%/남은 YY%, 남은 기본/별도 예비/실제 ETA**, 차단, 다음 액션을 간결하게 말한다. 자동 백그라운드 작업·다른 채팅에 실시간 메시지 전송을 약속하지 않는다.

## 무결성·비용·안전
- `LIVE_HANDOFF.md`와 `LIVE_STATE.json`은 이후 모든 새 채팅의 **최신 현황 정본**이다. 원격 커밋 전에 [`tests/test_handoff_bootstrap.py`](../../../tests/test_handoff_bootstrap.py) 검증을 실행할 수 있도록 파일 경로·필수 키·표시한 확인 결과를 유지한다.
- **SDK는 단순 URL/ZIP 해시만 알 뿐 내부 정확한 명령은 미검증**. SDK ZIP/소스나 비밀키/고객 정보·권한 없는 NAS 데이터를 Public GitHub에 올리지 않는다. 허구 명령을 만들지 않는다.
- 개발 종료를 선언하기 전에 인수인계를 완성하여 **새 채팅에 한 문장만 보내도 동일 지점에서 계속 가능**한지 스스로 교차 확인한다.


> **2026-10-24 전체 24일 마스터 진척표 도입(제품 진척 변화 없음):** [MASTER_PROGRESS.md](../../../MASTER_PROGRESS.md)와 단일 [JSON 정본](../../../data/master_progress.json). 10/24 일일 산출물 100%, 10/25 공식 G1 SDK/CLI·Agent 0% BLOCKED, G2~G6 합성 선행 결과와 정식 SDK 실증은 분리. 작업이 끝날 때마다 JSON→`python render_master_progress.py --write`→CI `--check`를 같은 GitHub 커밋으로 반영. 실제 작업시간 미계측.
