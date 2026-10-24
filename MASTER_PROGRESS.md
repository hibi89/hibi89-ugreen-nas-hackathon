# MASTER_PROGRESS — UGREEN NAS AI Hackathon

> **자동 생성 파일입니다. 직접 수정 금지.** 단일 JSON 정본: `data/master_progress.json`. 갱신: `python render_master_progress.py --write`; 검증: `python render_master_progress.py --check`.
> 예정일과 실제 수행일은 별개. DONE은 **그날 정한 검증 범위만** 완료했음을 의미하며 실제 외부 API/운영/제출 성공과 다릅니다.
> 시간은 예상 작업·별도 안전 예비의 **미사용 작업 배정량**입니다. 외부 승인 대기 및 미계측 실투입시간은 포함하지 않습니다.

> **외부 차단과 합성 선행개발은 실제 SDK·NAS 사용 가능 판정이 아닙니다.**
**전체 24일 / 완료 2 / 부분 12 / 차단 3 / 미착수 7**

**다음 실행 포인터: `UGR-D02`** · 원래 일정: `docs/UGREEN_DAILY_EFFORT_PLAN_20261024.md`

| ID | 예정일(KST) | 원래 작업 | 상태 | 해당 일 완료율 | 남은 기본 | 남은 예비 | 실제 수행일 | 증거(경로·CI) | 검증 SHA | 회수 목표일 |
|---|---|---|---|---:|---:|---:|---|---|---|---|
| UGR-D01 | 2026-10-24 | 운영 문서 전환은 이미 진행. 과거 실측시간 없음 | DONE | 100% | 0h | 0h | 2026-10-24 | docs/roles/lead/DAILY_PROGRESS.json | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D02 | 2026-10-25 | G1 공식 Kit 재접근: 기존 실패와 다른 합법적 경로 한 가지 | BLOCKED | 0% | 1.5h | 1.5h | 2026-10-24 | docs/roles/lead/G1_ZIP_METADATA_RECOVERY_20261024.md | e06f3a2b3ec4a3f6ad2300c5f7505bcb4b6e819a | 2026-10-26 |
| UGR-D03 | 2026-10-26 | 공식 CLI·등록 Expert Agent·권한 자료 추출 또는 무료 문의 | BLOCKED | 0% | 1.5h | 1.5h | 2026-10-24 | docs/architecture/G1_PUBLIC_CATALOG_BINDING_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | 2026-10-27 |
| UGR-D04 | 2026-10-27 | G1 게이트와 G2 데이터 계약 초안·기술 선택 | BLOCKED | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G2_EVIDENCE_CONTRACT_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | 2026-10-27 |
| UGR-D05 | 2026-10-28 | 필수 납품 목록/허가 폴더/증거 연결 규칙 구현 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G2_EVIDENCE_CONTRACT_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D06 | 2026-10-29 | 누락 탐지 합성 케이스·회귀 테스트·수정 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G5_CORE_EDGE_SCENARIOS_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D07 | 2026-10-30 | 서로 다른 최종본 후보 판정 규칙 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G3B_VERSION_CANDIDATES_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D08 | 2026-10-31 | 버전 충돌·모호성 합성 테스트 및 정리 | PARTIAL | 0% | 2h | 2h | 2026-10-24 | docs/architecture/G3B_VERSION_CANDIDATES_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D09 | 2026-11-01 | 권한/외부 전송/개인정보 정보흐름 위협모델 | PARTIAL | 0% | 2h | 2h | 2026-10-24 | docs/architecture/G3C_POLICY_GUARD_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D10 | 2026-11-02 | 권한 거부·부분조회·PII 미지원 에지 테스트 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G5_CORE_EDGE_SCENARIOS_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D11 | 2026-11-03 | 단일 SKILL.md와 참조문서 골격 통합 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | skill/projectready-nas/SKILL.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D12 | 2026-11-04 | 오케스트레이션 연결 및 I/O 계약 재점검 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G4_COMBINED_REPORT_OFFLINE_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D13 | 2026-11-05 | CORE1·CORE2·EDGE1 합성 시나리오 실행 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G5_CORE_EDGE_SCENARIOS_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D14 | 2026-11-06 | 지원 도구 검증(가능한 경우)과 ZIP 사전 검사 | PARTIAL | 0% | 2h | 1h | 2026-10-24 | docs/architecture/G7_ROUND1_PACKAGE_PREFLIGHT_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D15 | 2026-11-07 | 영문 제안서 10개 답변 초안 | DONE | 100% | 0h | 0h | 2026-10-24 | docs/submission/round1_proposal.json | 7432cc3701b92de9b9d187f4e00be5f3b0a79885 | — |
| UGR-D16 | 2026-11-08 | PDF 편집·렌더 검수와 SKILL 패키징 | PARTIAL | 0% | 2h | 2h | 2026-10-24 | docs/architecture/G7_ROUND1_PACKAGE_PREFLIGHT_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D17 | 2026-11-09 | 라이선스·PII·비밀·용량·링크·재현성 출시 검수 | PARTIAL | 0% | 1.5h | 1.5h | 2026-10-24 | docs/architecture/G7_ROUND1_PACKAGE_PREFLIGHT_20261024.md | 5772a8a97364a26155c238ea7af576bdd400dc1a | — |
| UGR-D18 | 2026-11-10 | UGREEN 조기 제출 시도 조건부 / KIC 조기 제출 보호 | NOT_STARTED | 0% | 1h | 0.5h | — | — | — | — |
| UGR-D19 | 2026-11-11 | PayPal 조기 제출 보호 / UGREEN 필수 오류만 | NOT_STARTED | 0% | 0.5h | 0.5h | — | — | — | — |
| UGR-D20 | 2026-11-12 | KIC 공식 마감 보호 — UGREEN 신규 개발 금지 | NOT_STARTED | 0% | 0h | 0.5h | — | — | — | — |
| UGR-D21 | 2026-11-13 | PayPal 공식 마감 보호 — UGREEN 신규 개발 금지 | NOT_STARTED | 0% | 0h | 0.5h | — | — | — | — |
| UGR-D22 | 2026-11-14 | UGREEN 예비 제출일, 재검증 및 최종 접수 | NOT_STARTED | 0% | 1.5h | 1.5h | — | — | — | — |
| UGR-D23 | 2026-11-15 | 영수증 및 필수 파일 확인, 실제 불합격 수정만 | NOT_STARTED | 0% | 0.5h | 1h | — | — | — | — |
| UGR-D24 | 2026-11-16 | 공식 16:45 KST 마감 이전 상태 확인 | NOT_STARTED | 0% | 0.25h | 0.75h | — | — | — | — |

## 보류·차단 / 다시 확인할 일

- **UGR-D02 (2026-10-25, 0%):** 실제 SDK/등록 Agent/권한/정식 validator 미검증 / 재검토: 주최자 공식 문서·기술지원 또는 허가된 참가자 환경에서 정확한 실행 근거 확보 / 회수일: 2026-10-26
- **UGR-D03 (2026-10-26, 0%):** 실제 Expert Agent 등록·권한·라이선스/응답 근거 부재 / 재검토: 공식 설치 환경에서 실제 명령·권한/응답 검증 또는 주최 측 지원 근거, 없으면 BLOCKED 유지 / 회수일: 2026-10-27
- **UGR-D04 (2026-10-27, 0%):** 실지원 SDK 계약 미확정으로 G2 승인 게이트 차단 / 재검토: 공식 설치 환경에서 실제 명령·권한/응답 검증 또는 주최 측 지원 근거, 없으면 BLOCKED 유지 / 회수일: 2026-10-27

## 이미 선행한 작업과 검증 경계

- UGR-D01 (2026-10-24): 10/24 실제 오프라인 G2/G3b/G3c/G4/G5/G6 선행 구현은 합성 검증; 원래 10/24 제품 개발 배당 0h, 실제 시간 미계측. 공식 SDK/CLI/NAS 미검증.
- UGR-D02 (2026-10-25): 공식 공개 SDK ZIP/SHA, CLI 카탈로그 9개 read 동작의 파라미터를 10/24 선행 정적 확인. 실제 Agent 호출·validator는 차단. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D03 (2026-10-26): file-agent/document-agent 이름·read 파라미터는 카탈로그 확인; 실제 등록·권한·라이선스 미검증. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D04 (2026-10-27): G2 임시 증거/미검증 계약 선행 완료. 실제 공식 Agent I/O 근거 없어 계약 동결 불가. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D05 (2026-10-28): presence.py 합성 구현·테스트 완료; 공식 NAS read adapter와 권한/완전성 미검증. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D06 (2026-10-29): 누락·부분 결과·권한 거부 합성 테스트 선행; 실제 API 테스트 미실행. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D07 (2026-10-30): version_candidates.py 합성 구현 선행; 실제 NAS 메타데이터/해시 연동 미검증. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D08 (2026-10-31): 버전 후보 모호성 합성 검증 선행; 실제 최종본 승인/지원 범위 미확인. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D09 (2026-11-01): policy_guard.py 읽기 전용·권한 정책 선행; 실 NAS/PII 데이터흐름 미검증. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D10 (2026-11-02): 권한 거부·불완전 조회 합성 테스트 선행; 실제 사용자/PII 검증 미실행. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D11 (2026-11-03): 4개 Markdown Skill 후보 오프라인 preflight PASS; 공식 Uliya validator·Agent 연결 미실행. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D12 (2026-11-04): combined_report.py 합성 통합 보고 선행; 실제 Agent I/O 연결 미실행. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D13 (2026-11-05): CORE1/CORE2/EDGE1 합성 검증 완료; 실제 NAS 실행 미실행. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D14 (2026-11-06): Skill 4개 Markdown 파일 사전검사 선행; 공식 validator 미실행. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음.
- UGR-D15 (2026-11-07): 2026-10-24 선행: 10개 공식 Round1 영문질문 351/500단어 초안 DONE. GitHub 소스 7432cc3701b92de9b9d187f4e00be5f3b0a79885에서 183/183 오프라인 CI PASS, MASTER/인수인계 CI PASS. 로컬 A4 PDF 1페이지 4,484 bytes 생성·렌더/텍스트 확인; 참가자 최종 승인·Devpost 제출은 NOT_SUBMITTED. Official Round 1 question titles corrected to source Rule 4 verbatim in new draft code; prior PDF draft STALE. Corrected PDF creation and verification are pending GitHub Actions; D15 draft status stays DONE. GitHub Actions 40076525716 exact official questions appeared correctly in newly regenerated 4722-byte one-page searchable PDF; still draft and not submitted.
- UGR-D16 (2026-11-08): ZIP 구조/재현성 도구 선행; 제출 영문 PDF 미생성. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음. 2026-10-24 provisional A4 PDF locally rendered (one page, 4,484 bytes) and readable; source renderer tools/render_round1_proposal_pdf.py; still PARTIAL because approved final PDF and packaged ZIP/receipt are absent. G8 2026-10-24: automated Round1 PDF/ZIP/manifest DRAFT generation and artifact-upload workflow added; awaiting remote CI proof. Final participant-approved PDF/ZIP, official validation and Devpost submission still NOT_DONE. VERIFIED: GitHub Actions 40076525716 succeeded, created PDF 4722 bytes/1 page and ZIP 6004 bytes/4 directly-linked Markdown members. CI artifact ID 12553276854, PREVIEW_NOT_SUBMITTED. D16 remains PARTIAL pending participant approval/final package/real Devpost receipt.
- UGR-D17 (2026-11-09): 출시 ZIP 구조·비밀 패턴 오프라인 사전검사; 공식 라이선스·PII·validator 최종 검수 미실행. 정식 일일 범위의 완료 가중치가 없으므로 0%를 임의 상승시키지 않음. G8 ZIP SHA256 + per-member hashes, PDF searchable questions, size, 4-Markdown entries checked by candidate bundle script; automated result pending CI. License/privacy review remains unverified. Candidate ZIP manifest includes archive SHA256, file hashes, file/size and PDF searchable ten-heading checks; offline-only, no official validator or license/PII attestation.

## 운영 의무

1. 모든 예정일을 JSON에서 보존하고 날짜를 건너뛰어 삭제하지 않습니다. 선행 수행은 실제 수행일을 기록하되 다음 미완료 날짜를 자동 완료 처리하지 않습니다.
2. 작업 완료·부분중단·차단 변경 때 **JSON 정본 → 이 Markdown 재생성 → CI --check**를 같은 GitHub 커밋으로 반영합니다. 과거 운영문서는 이력이며 충돌하면 JSON·실제 테스트 증거를 확인합니다.
3. DONE/100%는 해당 날짜 범위만 뜻합니다. 실제 PayPal/DAKER/NAS 접근·실고객·운영 배포·Devpost는 별도 외부 영수증 없으면 NOT_TESTED로 유지합니다.
4. 예비시간을 기본시간에 합쳐 '실제 사용시간'이라고 주장하지 않습니다. 조건이 충족되지 않은 BLOCKED 행은 새 날짜가 와도 DONE으로 바뀌지 않습니다.
