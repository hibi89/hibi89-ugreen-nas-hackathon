# UGREEN ProjectReady: 작업 순서 유연화·선행 개발 규약

사용자 승인 2026-10-24 KST. 상위 정본: https://github.com/hibi89/hackathon-command-center-2026/blob/main/docs/WORK_ORDER_FLEX_POLICY_20261024.md

## 작업 시작 전
- `lead/ugreen` 최신 HEAD, `LEAD_ACTIVE_WORK.md`, `CARRYOVER_TASK_SCHEDULE_20261024.md`, `DAILY_PROGRESS.md`, `DAILY_PROGRESS_REPORTING_PROTOCOL.md`, `UGREEN_DAILY_EFFORT_PLAN_20261024.md`를 조회한다.
- **달력상 내일·모레 업무도 독립 검증 가능하면 선행 실행 허용**. `ㄱ` 때 단순 날짜순이 아니라 의존성이 해결된 가장 효과적인 READY 업무를 구현→테스트→원격 커밋한다.
- G1 공식 SDK CLI/Expert Agent/Skill 형식, 외부 실제 NAS는 원본 문서·런타임을 검증할 때까지 `BLOCKED` 또는 `NOT_TESTED` 유지. G2/G3b 등 합성 모듈은 공식 API 동작을 가정하지 않는 범위만 DONE 허용하고 G1 게이트를 우회하지 않는다.
- 기존 선행 개발 G2/G3b 합성 코드·테스트 재구현 금지. G1 접근 불가라면 접근 독립적인 안전 정책·반례·검증 로그를 우선 수행하되 스펙과 실제 NAS 재현 필요성을 명시한다.
- 오늘 10/24의 100%는 **그날 계획 산출물만** 뜻한다. 미래 예정 G1의 100점/차단 여부와 혼동하지 않는다. 미래 과제의 완료 시 원래 예정일·실제 실행일·독립 작업 완료율을 기록하고 **이중 집계하지 않는다**.
- 원본 일별 보수적 투입시간·별도 예비·11/10 내부 목표·공식 11/16 16:45 KST 마감은 그대로. SDK 접근 불가 시간은 따로 `UNKNOWN`; 0원 신규 비용, SDK/원본 재배포·의심 ZIP 무단 실행·실데이터 전송 금지.
- `LEAD_ACTIVE_WORK.md` 및 `DAILY_PROGRESS.md`/JSON·`STATUS.md`/HANDOFF·`TO_UGREEN_LEAD.md`에 작업ID·계획/실행 날짜·선행조건·차단·테스트·실환경 여부·원격 SHA·남은 기본/복구 예비시간·순서 변경 이유를 기록.

**순서는 유연하게, 공식 지원/실장비 검증 기준은 엄격하게 유지.**
