> **ARCHIVED / NON-EXECUTABLE — 2026-10-24 KST:** Old single-worker-chat queue is retired by participant decision. The READY/BACKLOG/REVISION instructions appearing below are historic; DO NOT launch or continue a separate worker chat from these instructions. UGREEN lead executes the work itself in `lead/ugreen` using `docs/roles/lead/LEAD_ACTIVE_WORK.md` and `LEAD_FULLSTACK_PROTOCOL.md`. Worker report UGR-001 was BLOCKED at latest observed feature HEAD; no auto release of UGR-002.

# UGREEN BACKLOG — 미래 순차 작업 (지금 실행 금지)
CURRENT_TASK가 유일한 활성 업무다. **담당자 채팅은 한 개**이며 작업별 TARGET_BRANCH로 전환.

| 순서 | 업무 | TARGET_BRANCH | KST 계획 | 진입 조건 | 상태 |
|---|---|---|---|---|---|
| 1 | UGR-001 공식 SDK/CLI 기술 조사 | feature/missing-files | 10/24~26 | 현재 READY | **READY** |
| Gate | G2 총괄 SDK 결과 검수·데이터 계약 | lead/ugreen | 10/27 | UGR-001 ACCEPTED | 대기 |
| 2 | UGR-002 필수 파일 누락 | feature/missing-files | 10/28~29 | G2 승인/새 READY | 대기 |
| 3 | UGR-003 버전 충돌 | feature/version-conflicts | 10/30~31 | UGR-002 검수/새 READY | 대기 |
| 4 | UGR-004 정보보호 위험 | feature/privacy | 11/01~02 | UGR-003 검수/새 READY | 대기 |
| Gate | G4 Skill 통합 | lead/ugreen | 11/03~05 | UGR-004 검수 | 대기 |
| Gate | G5~G8 기술 검사·제안서·최종 제출 | lead/ugreen | 11/06~10 | G4 완료 | 대기 |

각 Task를 마친 작업자는 지정 feature 브랜치 TO_UGREEN_LEAD에 DONE_FOR_REVIEW/BLOCKED 보고. 총괄만 NEXT Task/REVISION을 READY로 개방. 예정 날짜가 왔다는 이유만으로 병렬 작업하지 않는다. 공식 마감 2026-11-16 16:45 KST. 현금 비용 0원 목표.
