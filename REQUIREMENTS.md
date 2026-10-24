# UGREEN 요구사항 — 2026-10-24 스냅샷

## 확정된 운영 제약
- 참가 신청 완료 화면 사용자 제공(2026-10-24). Devpost 제출 프로젝트 생성과 공식 최종 제출은 **미완료**.
- 공식 제출 마감: **2026-11-16 16:45 KST**. 대회 공식 규정: https://ugreenhackathon.devpost.com/rules
- 예선: UGREEN Developer Package/Uliya Standard 기반 SKILL.md 및 허용된 참고 Markdown으로만 구성된 ZIP, 500영단어 이하 영문 PDF(1MB 이하). ZIP 압축/해제 10MB 이하, 파일당 1MB 이하, 100개 이하. 예선 실제 NAS 불필요.
- 실제 참가자 1명, AI 총괄 1명+기능 작업자 3명, `main` 통합 코드·분리 브랜치.

## 주제·기능 (아직 사용자 최종 확정 아님)
- 잠정 제품: **NAS 프로젝트 문서·파일 관리 AI Skill (잠정)**.
1. 필수 파일 누락 (`feature/missing-files`): 구체 데이터 계약/구현 세부/가용성은 담당 총괄이 검증 후 설계한다.
2. 중복·버전 충돌 (`feature/version-conflicts`): 구체 데이터 계약/구현 세부/가용성은 담당 총괄이 검증 후 설계한다.
3. 개인정보 노출 위험 (`feature/privacy`): 구체 데이터 계약/구현 세부/가용성은 담당 총괄이 검증 후 설계한다.
- 대회 총괄은 **완성 가능한 핵심 MVP 1개 우선** vs **세 기능 동시 구현**을 비교(기술성·기간·심사·운영비)하고 최종 사용자에게 결정을 요청한다. 사용자 승인 전 기능 범위를 확정하거나 축소하지 않는다.

## 보안·상태
- 공식 규정/SDK 최신 확인, 외부 서비스 계정/API 허용 범위·비용·Rate, 로컬/원격 실행 환경을 선검토한다.
- **현재 실제 기능·테스트·API·배포 0건/미검증**; 문서만 마련된 단계. NAS Skill CLI/권한/개발 패키지 미확인. 실제 NAS 하드웨어 검증은 본선 진출 후 원격 테스트만 가능. 개인 데이터 외부 전송·무단 삭제 금지.

## [최신 2026-10-24] 사용자 위임에 따른 총괄 선택
- 범용 NAS 파일 검사(A)와 특정 프로젝트 납품 준비 판정(B)을 비교해 **B ProjectReady NAS(가칭)**를 독립 운영의 우선 방향으로 선택.
- 단일 Skill; 지원된 NAS 검색/문서 처리만 사용, 누락/충돌/정보노출은 지원 가능한 범위까지만 분석. 검사 불가 시 'Not checked', 원본/개인정보 보호 우선.
- 세 feature는 역할 분리일 뿐 별도 제출 3개가 아님. 신규 유료 결제 0원. 조기 제출 11/10 KST.
- 공식 Kit CLI 미검증: G1 기술 검증 전 세부 구현 확정 금지. [실행 계획](docs/UGREEN_EXECUTION_PLAN_20261024.md).


## FINAL USER-APPROVED DECISION — 2026-10-24 KST
- **ProjectReady NAS product fixed:** a requirement-to-NAS-file-evidence-to-delivery Go/No-Go AI Skill, rather than a generic file cleanup tool. ONE submission, three worker responsibilities.
- **UGREEN-only schedule fixed:** official kit support study 10/25-26, data contract 10/27, workers 10/28-31, integrated Skill 11/03, technical checks 11/06, PDF/ZIP frozen 11/09, **internal final Devpost submission target 11/10 KST**. **Official Round 1 deadline 11/16 16:45 KST**.
- **Zero incremental cash spending target**; new paid models/API/server/NAS not authorized. Existing subscriptions and work time excluded.
- Source of truth: [approved execution plan](docs/UGREEN_EXECUTION_PLAN_20261024.md) and [worker instruction](docs/roles/lead/WORKER_ASSIGNMENTS_20261024.md). This approval supersedes old 'tentative product' and 11/14 target statements above.
- **Actual execution:** Devpost registered, not created/submitted. No actual Uliya CLI archive internal study, SDK/NAS run, product tests or CI yet. Do not claim success until verified. Worker chats not automatically assigned.
