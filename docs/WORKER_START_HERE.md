# UGREEN 공통 담당자 — START_HERE
**기능별 3개 채팅 대신, UGREEN 공통 작업자 채팅 하나만 사용한다.** 총괄이 작업을 배정하면 같은 채팅에서 역할·브랜치를 전환한다.

## 모든 턴의 필수 순서
1. GitHub **hibi89/hibi89-ugreen-nas-hackathon**, 브랜치 **lead/ugreen**의 **docs/dispatcher/CURRENT_TASK.md** 최신 버전을 먼저 읽어 TASK_ID / STATUS / TARGET_BRANCH / 수용 기준 확인.
2. STATUS=READY이고 해당 TASK_ID가 아직 작업자 보고서에 DONE_FOR_REVIEW 또는 BLOCKED로 기록되지 않은 경우에만 시작. 이미 보고됐으면 중복 실행하지 않고 **총괄 검수 요청**.
3. TARGET_BRANCH 최신 HEAD 조회 → 해당 브랜치 HANDOFF.md / STATUS.md / AGENTS.md / REQUIREMENTS.md / 역할 OPERATIONS.md / TO_UGREEN_LEAD.md 읽기 → CURRENT_TASK의 업무만 수행.
4. 결과를 오직 TARGET_BRANCH에 커밋·푸시하고 그 기능의 TO_UGREEN_LEAD.md에 TASK_ID / DONE_FOR_REVIEW 또는 BLOCKED / 증거 / 실제 테스트 / 미검증 / 차단 / SHA를 보고. 사용자에게 최신 원격 SHA 반환.
5. 이후 총괄의 검수 및 CURRENT_TASK 새 REVISION 발행 전에는 다른 역할·브랜치에 착수하지 않는다. 같은 채팅에서 사용자가 '최신 작업 확인하고 진행'이라고 말하면 최신 지시를 다시 읽고 그때 지정된 브랜치로 이동.
6. STATUS=LEAD_GATE/PAUSED/CLOSED라면 실행하지 말고 대기 보고.

## 충돌 시 우선순위
최신 CURRENT_TASK > 공통 시작 안내 > 기능 브랜치의 과거 문서/채팅 기억. 예전 '3명 개별 채팅' 가정은 폐기. 타 대회 작업은 절대 섞지 않는다.

## 안전
- Public Repo, 유료 신규 비용 0원. 민감 파일·실 사용자 PII·토큰·비밀번호·.env·재배포권 없는 개발 Kit 업로드 금지.
- 허용 CLI 확인 전 임의 명령·실 NAS 성공 주장을 하지 않는다.
- 지정 feature 브랜치 외 lead/ugreen, main, 다른 feature 브랜치 수정 금지.
- GitHub만으로 다른 채팅이 자동 실행되거나 총괄에게 자동 알림이 가지 않는다. 작업 후 사용자에게 총괄 검수 요청을 안내.

## 새 담당자 채팅 첫 메시지
너는 UGREEN의 공통 작업 담당자다. GitHub lead/ugreen 브랜치의 docs/WORKER_START_HERE.md와 docs/dispatcher/CURRENT_TASK.md를 확인하고, READY 상태 업무 하나를 지정 feature 브랜치에서 실제 수행해. 작업 증거와 TO_UGREEN_LEAD 보고를 커밋하고 원격 SHA를 알려줘.

- [현재 지시](dispatcher/CURRENT_TASK.md)
- [후속 대기열](dispatcher/BACKLOG.md)
- [제품 일정](UGREEN_EXECUTION_PLAN_20261024.md)
