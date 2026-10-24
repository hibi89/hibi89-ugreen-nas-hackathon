# UGREEN NAS AI Hackathon 총괄 운영 절차

총괄 전용 브랜치 **`lead/ugreen`**. 책임은 UGREEN NAS AI Hackathon 제품 아키텍처·기술 검증·제출 및 아래 기능 담당 세 AI의 업무 감독. 통합 총괄은 개발하지 않고 **전체 일정·위험**을 감독한다.

## 모든 신규 지시 이전 필수 작업
1. `feature/missing-files` HEAD와 `docs/roles/missing-files/TO_UGREEN_LEAD.md` 확인 — 필수 파일 누락 탐지
2. `feature/version-conflicts` HEAD와 `docs/roles/version-conflicts/TO_UGREEN_LEAD.md` 확인 — 중복·버전 충돌 탐지
3. `feature/privacy` HEAD와 `docs/roles/privacy/TO_UGREEN_LEAD.md` 확인 — 개인정보 노출 위험 탐지

각 최신 상태를 확인한 뒤 `docs/roles/lead/MESSAGE_REVIEW.md`에 조회 시각(KST), 브랜치 SHA, 신규/보류/해결 항목과 결정 기록. 메시지함을 읽지 못했으면 **미확인**으로 남기고 기존 지시와 충돌하는 새 지시를 금지.

## 중요한 작업 종료
- 소스·테스트·CI·API·브라우저/서비스 검증 대조 → `docs/roles/lead/STATUS.md`·`docs/roles/lead/HANDOFF.md`·`docs/roles/lead/TO_HACKATHON_LEAD.md` **같은 작업에서 최신화** → 원격 SHA 검증.
- 기능 담당자는 자기 feature 브랜치만, 총괄은 `lead/ugreen`의 운영 문서·설계와 검증된 통합 PR만 관리.
- 실제 결제/개인 데이터/유료 서비스·권한/주제/범위 변경 등은 사용자 승인. 원본·보안 보존.

## 새 대화의 필수 독해
`lead/ugreen`의 `docs/roles/lead/HANDOFF.md` → `STATUS.md` → `OPERATIONS.md` → 루트 `AGENTS.md` → `REQUIREMENTS.md` → 기능 메시지함 세 곳 → GitHub HEAD와 실제 소스. 채팅방 간 알림·실시간 갱신을 가정하지 않는다.

## 2026-10-24 KST — 3개 해커톤 통합 일정 공시
- 이 브랜치 공식 일정: [docs/COMPETITION_SCHEDULE.md](../../COMPETITION_SCHEDULE.md). `UGREEN` 대회 총괄은 모든 주요 작업/지시 전에 본인 마감·전체 충돌·내부 조기 제출 목표를 검토한다.
- **현재 최우선:** 공식 11/16 16:45 KST까지 영문 500단어·1MB PDF 및 공식 Uliya 표준 SKILL.md 중심 ZIP.
- **내부 조기 제출 목표:** 11/14 KST (**주최 공식 마감이 아닌 프로젝트 목표**).
- **교차 위험:** KIC 11/12 10:00·PayPal 11/13 05:00 직후 제출. SDK/지원 CLI 확인 지연이 11/16 패키지 적격성 위험으로 확대.
- 제출 결과·기술 상태는 변경 없음. **등록 완료 ≠ 작품 생성 ≠ 최종 제출**; 주제·기능은 사용자 승인 전 잠정, CI/실 API/배포·시연 미검증.
- 발표/본선 등 후속 일정은 일정표 원문 기준. 중요 변경·지연·사용자 일정 개입은 총괄 상위 보고를 갱신하고 전체 총괄에게 전달할 것.

- 지시 전 세 기능 담당자의 TO_UGREEN_LEAD 메시지함 최신 SHA/원문도 검토한다. 공식 일정 변경을 확인했다면 주최 출처와 KST 변환 근거를 함께 기록한다.


## [2026-10-24 최신] 1개 레인 운영 (사용자 확정)
- UGREEN 기능 작업자 **동시 활성 최대 1명**. 총괄은 설계/검수/인수인계를 수행하되 작업자 3명을 한꺼번에 동원하지 않는다.
- 정해진 순서: missing-files(10/28~29) → version-conflicts(10/30~31) → privacy(11/01~02) → 총괄 통합(11/03~05). 계획표는 실제 인계 시 증거로 판단, 달력만으로 자동 활성화하지 않음.
- 활성화 전 3개 TO_UGREEN_LEAD 메시지함·SHA 읽기 → ACTIVE_WORKER 상태 확인 → **완료 증거 + 총괄 검수 + HANDOFF/STATUS** 뒤에만 다음 작업자 지시.
- 현재 ACTIVE_WORKER=none (G1/G2 리드가 먼저). 기능 브랜치는 그대로 두고 새 브랜치·자동 작업기 등록 없음.
- 이전 '3개 병렬 설계' 지시 및 10/28~31 한꺼번에 수행 일정은 본 운영 규칙으로 대체. 비용 0원·공식 마감·단일 제품 그대로.


## [최신 총괄 프로토콜] 공통 작업자 채팅 배정
- 작업자 채팅방 하나는 최신 CURRENT_TASK의 Task ID와 TARGET_BRANCH로만 일한다. 새 메시지나 날짜만으로 Task 전환하지 않는다.
- 총괄은 작업 종료 보고 후 [DISPATCH_PROTOCOL](DISPATCH_PROTOCOL.md)에 따라 지정 브랜치의 HEAD/실제 증거/TO_UGREEN_LEAD와 세 보고서를 확인, [REVIEW_LOG](../../dispatcher/REVIEW_LOG.md) 및 STATUS/HANDOFF/상위 보고 갱신, 다음 REVISION을 CURRENT_TASK에 게시한다.
- 현재 UGR-001 READY/feature/missing-files, 미실행. G2 검수 뒤 UGR-002/3/4 순차 개방. 작업자 3명 동시 접속/별도 채팅 필요 없음.
- 신규 결제/원본 변경/비밀정보 외부 전송/권한 확대는 사전 사용자 승인. 자동 채팅 알림·GitHub 락 없음.


## 2026-10-24 KST — 총괄·개발자 역할 통합 전면 개편(현행)
- 사용자 결정: 통합 총괄 1개 + UGREEN/KIC/PayPal 총괄 각각 1개, **전체 4개 채팅**. UGREEN 총괄이 단일 대화에서 직접 조사/설계/구현/테스트/검수/통합/제출 수행. 별도 순환 작업자 및 GitHub READY 디스패치 폐기.
- `lead/ugreen`은 향후 직접 개발·문서·검증의 기본 브랜치. 세 feature 브랜치는 원본 보존(삭제·force push 금지), 검증 후 선택적 소스 통합. `main`은 테스트 뒤 안정된 통합 기준으로 관리. 기존 `docs/dispatcher/CURRENT_TASK.md`, `BACKLOG.md`, `DISPATCH_PROTOCOL.md`, `docs/WORKER_START_HERE.md`는 읽기 전용 역사 기록이고 새 작업 호출 권한 없음.
- 기존 UGR-001 `feature/missing-files@4e74dc7b187e70ad72e906e042fdbf4c140940f8`: `SDK_CAPABILITY_MATRIX.md` 생성, `TO_UGREEN_LEAD.md`에 **BLOCKED(archive 내부 CLI/Expert Agent 등록·NAS 실 실행 미확인)** 보고. 공개 공식 문서 범위의 기술 표만 완료했고 SDK 런타임 성공 아님. 중복 다운로드 재시도 대신 공식 다운로드 가능 경로/지원팀/개인 소유 라이선스 문서 접근 등 다른 방법 검토. 다음 UGR-002 자동 착수 금지.
- 총괄 이전 기여: `docs/roles/lead/ROUND1_COMPLIANCE_AUDIT_20261024.md` 공식 공개 규정 점검. 새 `LEAD_ACTIVE_WORK.md`는 위 SDK 차단 해결·지원 CLI 증거 확보·G2 데이터 계약을 현재 1순위로 기록. 예선 기술 제약 검증 전 명령/버전/PII 기능 창작 금지.
- 내부 조기 제출 2026-11-10 KST, 공식 Round1 2026-11-16 16:45 KST. 실 NAS/CLI/CI/Devpost 제출 미완료. 추가 신규 지출 0원, 개인정보 외부 전송 승인 없음.
- 전환 전 기준 `lead/ugreen@b1a055911bf8a31d0643873507cdc52dccb67495`, `main@d8cd806cb2b3842a80a571fd09910ec370e2de17`. 새 커밋 SHA는 GitHub 원격 조회 결과를 최종 사용.
