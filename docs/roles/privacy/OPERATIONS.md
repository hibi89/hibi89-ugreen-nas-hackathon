# 개인정보 노출 위험 감지 — 담당 작업 규칙

- 대회: **UGREEN NAS AI Hackathon**. 역할 브랜치: `feature/privacy`. 이 브랜치 외 코드·데이터·`main`/총괄 브랜치 무단 수정 금지.
- 기능은 **잠정 설계 후보**이며 최종 사용자 확정 전. 총괄 `lead/ugreen`이 공식 Uliya 스펙/데이터 계약·우선순위와 통합 책임.
- 담당 후보 업무: 지원되는 읽기 범위에서 로컬 문서·파일명의 개인정보 위험 표식 및 최소 정보만 반환하는 요약. 데이터 외부 AI 업로드 금지
- 첫 단계: UGREEN 허용 CLI 및 지원 파일 형식·로컬 온디바이스 처리/모델 지원을 확인. PII 탐지는 오탐/누락과 권한 경계 분석 후만 설계
- 중요 제약: 사용자 개인정보 및 콘텐츠는 NAS 밖으로 무단 전송 금지. 지원되지 않는 OCR/로컬 LLM 능력을 전제로 하지 않는다.
- 새 채팅 시작: 해당 브랜치 `docs/roles/privacy/HANDOFF.md` → STATUS → OPERATIONS → 루트 AGENTS/REQUIREMENTS → 원격 실제 소스/HEAD 확인.
- 구현 전 API/CLI 허용 여부·권한/사용자 동의·오류 복구·재실행 안전·NAS 리소스/보안/제출물 ZIP 표준을 검토. 공식 Skill Developer Package 문서가 확인되지 않으면 구현 성공 주장 금지.
- Round 1 제출은 **영문 PDF(500단어 이내, 1MB 이하) + ZIP(Skill.md 및 직접 연결된 허용 Markdown)**. 저장소 운영 문서·스크립트를 제출 ZIP에 임의 포함 금지.
- 종료 시 `STATUS.md`, `HANDOFF.md`, `TO_UGREEN_LEAD.md` 함께 갱신/커밋/SHA 확인; 변경 없는 질의에 빈 커밋 금지.
