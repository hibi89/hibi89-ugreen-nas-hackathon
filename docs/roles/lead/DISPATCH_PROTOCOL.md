# UGREEN 총괄 — 단일 공통 작업자 디스패처 운영
2026-10-24 KST. 리드 전용 문서.

## 상태 기계
- **READY**: 총괄이 CURRENT_TASK.md에 TASK_ID/REVISION/TARGET_BRANCH/선행 HEAD/완료기준/유료 제한을 한 건만 공시.
- **RESULT**: 작업자는 지정 feature 브랜치의 TO_UGREEN_LEAD에 TASK_ID + DONE_FOR_REVIEW/BLOCKED 보고, 실제 산출물을 동일 feature 브랜치에 푸시. lead/ugreen은 읽기 전용.
- **REVIEW**: 사용자가 총괄에게 검수를 요청하면 CURRENT_TASK, 대상 feature HEAD/보고서/결과와 나머지 두 메시지함을 최신 재조회. 근거·테스트 PASS/FAIL·비용·안전 검증.
- **ACCEPTED**: 총괄이 REVIEW_LOG 및 lead STATUS/HANDOFF/TO_HACKATHON_LEAD를 기록. 총괄 선행 게이트(G2)가 있으면 먼저 완료하고 CURRENT_TASK를 LEAD_GATE로 둘 수 있음.
- **NEW READY**: 총괄만 다음 ID/REVISION/브랜치/완료기준으로 CURRENT_TASK 교체; 사용자 공통 작업자 채팅에서 '최신 작업 확인하고 진행'으로 재개.
- **REWORK/BLOCKED**: 현재 업무 해결 전 다음 병렬 개방 금지. 동일 접근 실패 2회 후 안전 대안/사용자 승인.
- **CLOSED**: 기능 완료, 총괄 통합·제출로 전환.

## 제한과 증거
- 이 방식은 문서 기반 업무조정이다. **실제 GitHub 상호배제 잠금, 자동 실행, 자동 보고/감지는 없다**.
- 작업자가 이미 같은 TASK_ID의 결과를 보고했으면 CURRENT_TASK가 READY라도 중복 수행 금지.
- 사용자의 개입은 한 번 새 작업자 채팅 개설, 담당자 종료 시 총괄 검수 요청, 최종 제출 확인 정도로 축소.
- 다른 대회는 별도 독립 레인. UGREEN 총괄은 KIC/PayPal 저장소 무단 수정하지 않는다.
