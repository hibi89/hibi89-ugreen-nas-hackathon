# UGREEN HANDOFF — 초기 인수인계 10항 (2026-10-24 KST)

1. **목표·확정 요구·기술**: UGREEN 해커톤에 1인 참가. 공식 마감 **2026-11-16 16:45 KST**. 주제 **NAS 프로젝트 문서·파일 관리 AI Skill (잠정)**. 상세 기능은 검증·사용자 승인 전 잠정.
2. **완료 작업·결정 근거**: Devpost 참가 등록 화면 확인. 사용자가 GitHub 빈 저장소를 생성. KIC의 5개 역할 분리/인수인계 방식을 참고해 운영 문서·브랜치를 준비하는 단계.
3. **테스트·검증**: 제품 테스트/실 API/CI/배포/현장 검증은 **0건**. 최초 GitHub 운영 문서 존재는 제품 완성을 뜻하지 않음.
4. **완료/진행/차단**: 참가 등록 완료; GitHub 역할 구조 초기화 중; 제품 주제와 데이터 계약 미확정; 공식 제출 프로젝트 생성·제출 미완료.
5. **오류 및 대안**: 확인된 실행 장애는 없음. 미검증: NAS Skill CLI/권한/개발 패키지 미확인. 실제 NAS 하드웨어 검증은 본선 진출 후 원격 테스트만 가능. 개인 데이터 외부 전송·무단 삭제 금지. 검증 불가를 장애로 단정하지 말 것.
6. **저장소·브랜치·경로**: `hibi89/hibi89-ugreen-nas-hackathon`, 기본 `main`; 총괄 `lead/ugreen`; 작업자 `feature/missing-files`, `feature/version-conflicts`, `feature/privacy`. 상위 총괄: `hibi89/hackathon-command-center-2026`.
7. **운영/Production**: 초기 정적 운영 문서만, Vercel/Production **미적용**. 개발 언어/호스팅/프로세스 아직 결정되지 않음.
8. **원본·백업·보안**: 새 빈 Public 저장소에서 시작, 기존 프로젝트/고객 데이터 없음. 인증 비밀·실계정 값·개인정보·비공개 제출 자산 커밋 금지.
9. **다음 단계·승인**: 총괄 채팅 설정/역할 문서 확인 → 공식 리소스/라이선스/API 제약 → 2개 설계안 비교 → 사용자 승인 → 기능 담당 개발. 범위·유료 사용·데이터 외부 전송·공개/권한 변경 사전 승인.
10. **검증 시점/기준 SHA**: 2026-10-24 KST 초기 문서 작성. 최신 원격 SHA는 항상 작업 시작 때 GitHub에서 조회하고 종료 시 보고. 자동 동기화 아님.

## [최신 운영 결정 | 2026-10-24 KST] UGREEN 자체 일정·무료 정책
- 제품 방향: **ProjectReady NAS(가칭), 단일 납품 준비 검수 AI Skill**를 총괄 추천안으로 채택(사용자 위임). 단 **실제 CLI 지원·PII/버전 검사 가능성은 미확정**.
- 이전 조기 제출 목표 **11/14는 11/10 KST로 변경**. 공식 Round 1 마감은 **11/16 16:45 KST** 그대로.
- 신규 결제 **0원 목표**, 기존 구독료·시간·전기/인터넷 제외. 신규 유료 API, 하드웨어, 호스팅 불필요.
- 상세: [UGREEN 독립 실행 계획](docs/UGREEN_EXECUTION_PLAN_20261024.md).
- 상태: 참가 등록 확인; 작품 생성/최종 제출 미완료; 기능·API·CI·NAS 실검증/Production 0건·미검증. 공식 다운로드 키트 내부 문서 확보가 다음 P0.
- 기존 스냅샷의 잠정 주제/11·14 목표와 다르면 **본 최신 운영 결정 우선**. 본 결정은 제품 개발 또는 제출 완료 증거가 아님.


## FINAL USER-APPROVED DECISION — 2026-10-24 KST
- **ProjectReady NAS product fixed:** a requirement-to-NAS-file-evidence-to-delivery Go/No-Go AI Skill, rather than a generic file cleanup tool. ONE submission, three worker responsibilities.
- **UGREEN-only schedule fixed:** official kit support study 10/25-26, data contract 10/27, workers 10/28-31, integrated Skill 11/03, technical checks 11/06, PDF/ZIP frozen 11/09, **internal final Devpost submission target 11/10 KST**. **Official Round 1 deadline 11/16 16:45 KST**.
- **Zero incremental cash spending target**; new paid models/API/server/NAS not authorized. Existing subscriptions and work time excluded.
- Source of truth: [approved execution plan](docs/UGREEN_EXECUTION_PLAN_20261024.md) and [worker instruction](docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md). This approval supersedes old 'tentative product' and 11/14 target statements above.
- **Actual execution:** Devpost registered, not created/submitted. No actual Uliya CLI archive internal study, SDK/NAS run, product tests or CI yet. Do not claim success until verified. Worker chats not automatically assigned.


## [최신 운영 변경 · 2026-10-24 KST] 해커톤 간 병렬, 해커톤 내부 기능 담당 1명씩 순차
- 사용자 확정: KIC·PayPal·UGREEN **세 대회는 동시에 진행**하되, **각 대회 내부에서는 기능 담당 AI를 한 번에 한 명만 활성화**한다. 3명 동시개발/병렬 설계 계획은 폐기한다.
- UGREEN 작업 순서: 총괄 공식 Kit·데이터 계약 10/25~27 → 작업자1 missing-files **10/28~29** → 총괄 인계 검수 → 작업자2 version-conflicts **10/30~31** → 인계 검수 → 작업자3 privacy **11/01~02** → 인계 검수 → 총괄 통합 **11/03~05** → 검사 **11/06** → PDF **11/07~08** → 동결 **11/09** → Devpost 조기 제출 **11/10**.
- **ACTIVE_WORKER=none** (아직 실 작업자 활성화/수신 확인 없음). 총괄이 1명 작업 완료 증거 SHA·테스트·보고서 및 차단을 검토하고 다음 담당자 활성화. 이전 작업자가 미완료면 다른 작업자 병렬 착수 금지.
- 계획된 제품 ProjectReady NAS 단일 Skill, 기존 feature 브랜치 3개, 공식 마감 **11/16 16:45 KST**, 추가 현금 지출 **0원 목표**는 그대로 유지한다.
- 공식 지원 CLI 미확인, 실제 실행·NAS·CI·작품 제출 미완료. 순차 작업으로 위험해지는 경우 **일정 또는 범위 변경 대안을 먼저 사용자에게 승인받는다**. 사용자 승인 없이 기능/품질 축소 금지.
- 운영 기준: [최신 일정](docs/UGREEN_EXECUTION_PLAN_20261024.md), [순차 담당 지시](docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md). 과거 병렬 표기보다 본 최신 지시가 우선이다.


## [최신 2026-10-24 KST] 단일 공통 작업자 채팅 + GitHub 작업 디스패치
- 사용자 운영 결정: UGREEN 총괄 채팅 1개 + **기능 3역할을 순차 수행하는 공통 작업자 채팅 1개**. 더는 담당자별 채팅 3개를 만들지 않는다. 기능별 GitHub 브랜치 3개는 유지한다.
- **총괄이 다음 업무를 게시할 유일한 위치**: lead/ugreen의 **docs/dispatcher/CURRENT_TASK.md**. 작업자 채팅은 매번 최신 TASK_ID, STATUS, TARGET_BRANCH를 확인해 지정 브랜치에서만 수행한다.
- **최초 UGR-001 READY**: 공식 Uliya Skill Developer Package 실제 지원기능·CLI/Expert Agent/권한·모델·비용 조사, 대상 브랜치 **feature/missing-files**, 현재 베이스 SHA **9b3052bf82ad1a8a4844b1aeee699c0b759251dc**. 실제 실행/완료 미확인.
- 작업자는 자기 feature 브랜치에 증거·TO_UGREEN_LEAD.md의 DONE_FOR_REVIEW 또는 BLOCKED 보고만 작성, 리드·다른 브랜치 수정 금지. **총괄이 원격 SHA와 증거를 검수/수락한 뒤 새 ID/REVISION을 READY로 게시**할 때만 다음 역할로 전환.
- 시작 지침: [공통 작업자 입문](docs/WORKER_START_HERE.md) / [현재 작업](docs/dispatcher/CURRENT_TASK.md) / [예정 업무](docs/dispatcher/BACKLOG.md) / [검수 규약](docs/roles/lead/DISPATCH_PROTOCOL.md). 이 최신 운영 규칙이 이전 '3개 독립 채팅' 및 '세 명 동시 작업' 문구보다 우선한다.
- 기술 개발/SDK 실검증·CI/NAS·Devpost 제출은 아직 완료되지 않았다. UGREEN 11/10 조기 제출, 11/16 16:45 KST 공식 마감, 신규 현금 비용 0원 목표 유지. GitHub 문서만으로 AI 채팅 자동 실행·통지/잠금 기능을 제공하지 않는다.
