# 중복·버전 충돌 감지 — 담당 작업 규칙

- 대회: **UGREEN NAS AI Hackathon**. 역할 브랜치: `feature/version-conflicts`. 이 브랜치 외 코드·데이터·`main`/총괄 브랜치 무단 수정 금지.
- 기능은 **잠정 설계 후보**이며 최종 사용자 확정 전. 총괄 `lead/ugreen`이 공식 Uliya 스펙/데이터 계약·우선순위와 통합 책임.
- 담당 후보 업무: 해시·파일 크기·이름·메타데이터를 근거로 가능한 중복 파일·버전 차이를 찾아 사용자가 확인하도록 설명. 원본 변경 금지
- 첫 단계: UGREEN 공식 지원 CLI와 읽기 권한 검증 후 중복 정의(동일 해시 vs 유사 이름)·오탐율·샘플 테스트 설계 제안
- 중요 제약: 대용량 해싱 성능/권한과 압축된 스킬 표준을 확인. 파일 충돌 자동 해소·삭제·이동 금지.
- 새 채팅 시작: 해당 브랜치 `docs/roles/version-conflicts/HANDOFF.md` → STATUS → OPERATIONS → 루트 AGENTS/REQUIREMENTS → 원격 실제 소스/HEAD 확인.
- 구현 전 API/CLI 허용 여부·권한/사용자 동의·오류 복구·재실행 안전·NAS 리소스/보안/제출물 ZIP 표준을 검토. 공식 Skill Developer Package 문서가 확인되지 않으면 구현 성공 주장 금지.
- Round 1 제출은 **영문 PDF(500단어 이내, 1MB 이하) + ZIP(Skill.md 및 직접 연결된 허용 Markdown)**. 저장소 운영 문서·스크립트를 제출 ZIP에 임의 포함 금지.
- 종료 시 `STATUS.md`, `HANDOFF.md`, `TO_UGREEN_LEAD.md` 함께 갱신/커밋/SHA 확인; 변경 없는 질의에 빈 커밋 금지.
