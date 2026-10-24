> **ARCHIVED / NON-EXECUTABLE — 2026-10-24 KST:** Old single-worker-chat queue is retired by participant decision. The READY/BACKLOG/REVISION instructions appearing below are historic; DO NOT launch or continue a separate worker chat from these instructions. UGREEN lead executes the work itself in `lead/ugreen` using `docs/roles/lead/LEAD_ACTIVE_WORK.md` and `LEAD_FULLSTACK_PROTOCOL.md`. Worker report UGR-001 was BLOCKED at latest observed feature HEAD; no auto release of UGR-002.

# UGREEN CURRENT_TASK — 단일 공통 담당자 지시
2026-10-24 KST · 소유자 UGREEN 총괄 · 이 파일만 현재 실행권한을 부여한다.

## 단 하나의 활성 업무
- TASK_ID: **UGR-001**
- REVISION: **1**
- STATUS: **READY (담당자 작업 시작 미확인)**
- WORKER_CHAT: **하나의 공통 UGREEN 담당자 채팅**
- TARGET_BRANCH: **feature/missing-files**
- ROLE: **공식 Uliya Skill Developer Package 지원 기술 조사**
- BASELINE_SHA: **9b3052bf82ad1a8a4844b1aeee699c0b759251dc**
- TARGET_DATE_KST: **2026-10-26**
- SPENDING: **신규 현금 지출 0원**
- OTHER_ACTIVE_TASKS: **없음**

## 실제 수행할 일
1. lead/ugreen의 최신 CURRENT_TASK 내용, TARGET_BRANCH 최신 HEAD와 담당 브랜치의 TO_UGREEN_LEAD.md 확인. 동일 Task ID DONE_FOR_REVIEW/BLOCKED 기록이 이미 있으면 중복 수행하지 않고 총괄 검수만 요청.
2. 공식 Starter Kit https://ai.ugreen.com/pages/hackathon-starter-kit 를 실제 살펴보고 https://ugreenhackathon.devpost.com/rules 와 대조. 패키지 파일 접근 자체가 막히면 차단 사실과 무료 대응책 기록.
3. 패키지명/버전, Skill 표준, 허용 UGOS CLI 명령의 정확한 근거·입출력·권한, 등록 Expert Agent, NAS 파일·문서 조회, 버전/해시, PII, AI 로컬/외부 처리, 비용·사용량을 항목별 **CONFIRMED/UNSUPPORTED/UNVERIFIED**로 구분.
4. 공식 근거 문서 URL·섹션/파일 경로를 기재한 **docs/roles/missing-files/SDK_CAPABILITY_MATRIX.md**를 TARGET_BRANCH에서 생성. 다운로드된 라이선스 불명 자료나 비밀키 업로드 금지.
5. 같은 TARGET_BRANCH의 **docs/roles/missing-files/TO_UGREEN_LEAD.md**에 UGR-001, DONE_FOR_REVIEW 또는 BLOCKED, 검증 결과/미검증/차단·비용과 의사결정 필요사항을 보고.
6. TARGET_BRANCH에만 커밋·푸시, 원격 HEAD SHA를 확인하여 사용자에게 보고. lead/ugreen, main, 다른 feature 브랜치를 변경하지 않는다.
7. 다음 Task를 임의로 시작하지 말고 총괄의 실제 검수와 새 REVISION 지시를 기다린다.

## 총괄 수용 기준
- 확인된 기술/CLI/권한에 공식 출처 증거, 미확인 기능을 단정하지 않음.
- 모델·개인정보·외부 전송·유료 API 제한 명시, 가능하면 0원 대안.
- feature 브랜치 2개 보고 파일/정확한 작업 ID/원격 SHA.
- 총괄이 REVIEW_LOG와 STATUS/HANDOFF에 승인 기록을 남기기 전까지 Task는 완료 처리되지 않는다.

## 불변 운영
단일 WORKER 채팅, 현재 READY 업무 하나, 지정된 작업 브랜치 하나. BACKLOG는 미래 계획이지 실행 지시가 아니다. 채팅 간 자동 동기화/알림·실제 분산 락은 없다. 공식 11/16 16:45 KST, 내부 11/10 KST 목표.
