# 필수 프로젝트 파일 누락 탐지 — 담당 작업 규칙

- 대회: **UGREEN NAS AI Hackathon**. 역할 브랜치: `feature/missing-files`. 이 브랜치 외 코드·데이터·`main`/총괄 브랜치 무단 수정 금지.
- 기능은 **잠정 설계 후보**이며 최종 사용자 확정 전. 총괄 `lead/ugreen`이 공식 Uliya 스펙/데이터 계약·우선순위와 통합 책임.
- 담당 후보 업무: 프로젝트별 필수 파일 목록·폴더 구조를 검토해 누락/불일치 보고. UGREEN NAS 허용 파일 검색·메타데이터 조회와 데이터 권한 범위 내 읽기 전용
- 첫 단계: 공식 Skill Developer Package의 허용 CLI·파일 읽기/검색 권한·실제 입력/출력 스키마 확인. 미확인 명령·경로를 지어내지 않음.
- 중요 제약: NAS 실물 없음. 본선 원격 NAS 테스트 전 실제 동작 미검증; 외부 유출 및 사용자 승인 없는 파일 이동/삭제 금지.
- 새 채팅 시작: 해당 브랜치 `docs/roles/missing-files/HANDOFF.md` → STATUS → OPERATIONS → 루트 AGENTS/REQUIREMENTS → 원격 실제 소스/HEAD 확인.
- 구현 전 API/CLI 허용 여부·권한/사용자 동의·오류 복구·재실행 안전·NAS 리소스/보안/제출물 ZIP 표준을 검토. 공식 Skill Developer Package 문서가 확인되지 않으면 구현 성공 주장 금지.
- Round 1 제출은 **영문 PDF(500단어 이내, 1MB 이하) + ZIP(Skill.md 및 직접 연결된 허용 Markdown)**. 저장소 운영 문서·스크립트를 제출 ZIP에 임의 포함 금지.
- 종료 시 `STATUS.md`, `HANDOFF.md`, `TO_UGREEN_LEAD.md` 함께 갱신/커밋/SHA 확인; 변경 없는 질의에 빈 커밋 금지.
