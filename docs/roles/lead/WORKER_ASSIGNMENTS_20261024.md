# ProjectReady NAS — 순차 기능 담당자 운영 지시

> 2026-10-24 KST, 사용자 확정. **KIC·PayPal·UGREEN은 대회별 병렬, UGREEN 기능 작업자는 한 명씩 순차.** 이 문서는 lead/ugreen 계획이며 자동 채팅 배포·작업 개시가 아니다.

## 0. 활성 레인
- **ACTIVE_WORKER=none (현재)**. 총괄이 공식 Skill Kit와 G2 데이터 계약을 확인하기 전 기능 작업자는 활성화하지 않는다.
- 다른 담당자가 작업 중이면 새로운 담당자에게 개발을 시작시키지 않는다. 총괄이 원격 SHA, 테스트/검증 근거, TO_UGREEN_LEAD 메시지, STATUS/HANDOFF를 확인하고 명시적으로 다음 작업자를 지정한다.
- G3 순서는 W1 → W2 → W3이며 같은 시각 활성 기능 담당은 최대 1명이다. 기능 3개는 하나의 Skill로 통합하고 개별 제출하지 않는다.

## 1. 실행 순서 및 핸드오프
| 일자 KST | 활성 담당 | 산출물·검수 기준 |
|---|---|---|
| 10/25~27 | UGREEN 총괄만 | 공식 Uliya 지원 CLI·등록 Expert Agent·입출력 계약/권한/비용 확인; 미지원 기능은 미검증 |
| **10/28~29** | **W1 feature/missing-files** | 필수 산출물과 파일 증거 매칭·Not searched vs missing·권한 거부. 자기 브랜치 참조 Markdown/테스트/TO_UGREEN_LEAD 갱신 |
| **10/30~31** | **W2 feature/version-conflicts** | 상충 버전 후보·증거와 오탐 분석. 임의 최신 판정 및 미지원 해시 API 금지 |
| **11/01~02** | **W3 feature/privacy** | 최소 권한·외부전송 제한·실제로 지원되는 위험 확인만. 검사 불가 = NOT_CHECKED |
| **11/03~05** | UGREEN 총괄만 | 세 기능의 검증된 결과를 단일 SKILL.md + 직접 링크된 references Markdown으로 통합 |
| 11/06 | 총괄 | 공식 Skill 생성 도구 및 모의 테스트 3개 유형. 미검증은 실제 작동으로 주장하지 않음 |
| 11/07~08 | 총괄 | 영어 PDF 질문 10개, 500단어·1MB 이하, 출처/AI 도구/데이터 흐름 명시 |
| 11/09 | 총괄 | 제출 ZIP/PDF 구조·크기·안전·해시/백업 동결 |
| **11/10** | 총괄 지원 + 참가자 확인 | Devpost 조기 제출 영수증 확인 (공식 마감 **11/16 16:45 KST**) |

## 2. 개별 브랜치 계약
- 담당 W1: feature/missing-files, 공식 허용 폴더 조회와 필수 계약서 비교. 정상 7/7, 누락 2/7, 권한 부족/일부만 검색됨의 합성 사례.
- 담당 W2: feature/version-conflicts, 실 증거로 충돌 후보 반환, 두 버전 모두 존재하는 경우 최신본 자동 선택 금지. 메타데이터 부족/미지원 API 예외.
- 담당 W3: feature/privacy, 읽기 범위 제한·민감정보 의심 출력 최소화 및 외부 전송 차단. 지원되지 않는 개인정보 내용 분석은 검사 안 됐음을 명시.
- 공통 출력 계약(가안): {scope, requirement_id, verdict: PASS|FAIL|REVIEW|NOT_CHECKED, evidence_refs, reason, limitations, next_action}. 실제 CLI 형식 아님.
- 각 담당은 **자신의 브랜치** HANDOFF → STATUS → AGENTS → REQUIREMENTS → OPERATIONS를 먼저 읽고, 끝나면 자기 TO_UGREEN_LEAD.md에 원격 SHA·출처·테스트·실패·미검증·다음 작업을 남긴다.
- 사용자 원본 수정·고객 실제 PII·.env/토큰·외부 전송·유료 API는 금지 또는 사전 승인. 신규 지출 0원 유지.

## 3. 지연 시 판정
- 개별 담당의 검수 실패·중단 시 다른 담당자를 병렬로 켜지 않는다. 원인/재시도 1회/대안 보고 후 사용자 승인으로 일정 조정.
- 총괄은 세 담당자 메시지함을 읽을 수 있으나 **작업자 활성화는 항상 한 명씩**.
- [최신 전용 일정](../../UGREEN_EXECUTION_PLAN_20261024.md) 및 [상위 보고](TO_HACKATHON_LEAD.md) 참조.

## [최신 2026-10-24] 실제 실행 명령은 공통 디스패처
- 기존 W1/W2/W3 날짜·담당 설명은 참고용이다. 각 역할마다 별도 AI 채팅을 만들지 않는다.
- 공통 작업자 채팅의 유일한 실행 지시는 [CURRENT_TASK](../../dispatcher/CURRENT_TASK.md)이며, 매번 지정된 TARGET_BRANCH에서만 작업한다. 사용자가 같은 채팅을 재사용한다.
- 최초 UGR-001 기술능력 조사 READY, feature/missing-files. [WORKER_START_HERE](../../WORKER_START_HERE.md)와 [BACKLOG](../../dispatcher/BACKLOG.md) 참조.
- 각 Task 수락/새 Task 배정은 총괄만 담당한다. 신규 유료 서비스 사용 금지, 개인정보 보호 및 Skill 개발 실검증 구분 유지.
