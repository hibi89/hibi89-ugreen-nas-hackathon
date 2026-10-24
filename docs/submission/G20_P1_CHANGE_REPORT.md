# G20 P1 — ProjectReady NAS 수정·비교 보고서

## 범위와 출처

- 검수 대상은 공식 Creator 결과로 전달된 원본 `SKILL.md`이며, 원본 SHA-256 `e1b071666b836cc464147821d7823bc3061c757434697d9a64250d4a9abd5b4a`와 일치함을 먼저 확인했다.
- 이 수정은 Creator를 다시 실행해 만든 결과가 아니다. 승인된 P1 보완을 위해 별도 검수 복사본의 위임 지시 부분만 편집했다. 원본 로컬 파일과 기존 GitHub Skill은 변경하지 않았다.
- 기준은 `hibi89/hibi89-ugreen-nas-hackathon` 원격 `lead/ugreen` HEAD `6a660075edd1de5f01c10a31e304902fbecafe2c`이다. 기준 Skill의 Git blob SHA-1은 `5a4d421cc46a3bd93ecdae03fc8064f083d07fd1`이다.
- 수정된 `name`은 `projectready-nas`이며 공식 검사기 SHA-256은 `SKILL.md` 실물 바이트와 일치한다.

## P1 수정 내용

기존 위임 예시는 “요청에 제공된 경로” 및 “file-agent가 반환한 참조”라는 대화 문맥 의존 문구만 사용해, 하위 Agent에게 실제 승인 폴더·체크리스트·버전 후보·문서 참조·질문이 전달된다는 보장이 없었다.

수정본은 다음을 매 호출의 필수 payload로 명시한다.

- `file-agent`: 실제 승인된 폴더 경로, 모든 필수 상대경로, 사용자 정의 버전 후보 패턴과 대상 항목, 읽기 전용 제한을 지시문에 직접 포함한다. 값이나 승인이 없거나 범위를 벗어나면 호출하지 않는다.
- `document-agent`: 첫 Agent가 실제 반환한 정확한 파일 참조와 버전 후보를 나열하고, 해당 파일별 별도 내용 검토 승인과 사용자의 정확한 질문을 지시문에 직접 포함한다. 지원 action의 `file`/`query` 입력으로 범위를 보존할 수 없으면 중단한다.
- 앞 단계가 반환한 실제 근거만 다음 단계에서 사용한다. 이전 대화의 문맥이나 “위 파일” 같은 암묵적 참조에 의존하지 않는다.
- 예시 경로·문서명·질문은 모두 합성 예시로 표시했다. 실제 NAS 경로나 개인 문서는 파일에 넣지 않았다.

## 유지한 정책 및 비교 결과

기존 Skill과 대조해 소유자 승인 범위 고정, 읽기 전용, 민감 항목 조회 금지 및 `[restricted item]` 마스킹, 완전한 조회 증거가 있을 때만 `MISSING`, 부분·거부·불명확 결과의 `NOT_CHECKED`, 복수 버전 `VERSION_REVIEW`, 별도 문서 내용 승인, 근거 없는 `READY` 금지를 유지했다. `PRESENT`/`MISSING`/`NOT_CHECKED` 의미와 `READY`/`BLOCKED`/`NEEDS_REVIEW` 판정도 바꾸지 않았다.

기존 `lead/ugreen` 및 `main`은 수정하지 않는다. 이번 원격 변경 범위는 별도 `review/ugreen-official-creator` 브랜치에 새 검수 Skill, 검사 결과 JSON, 이 보고서 세 파일뿐이다. 병합·SkillHub 게시·Devpost 제출은 하지 않는다.

## 공식 검사 결과

설치된 공식 `uliya-skill-kit`의 `scripts/check-skill.mjs`로 수정본을 검사했다. 첫 검사에서는 오류 0, 경고 1(`DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE`)이 나왔다. 두 번째 Agent가 첫 Agent의 실제 결과만 사용한다는 문장을 명시하고 재검사했다.

- 최종 결과: `static-pass`
- 검사 형식 / catalog: `2.0.0` / `2.0.0`
- 오류 / 경고 / 정보: `0 / 0 / 0`
- 진단: 없음
- 수정본 Skill SHA-256: `164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead`
- 민감정보를 제거한 JSON의 SHA-256: `92a6891b0889a89cd09f16ed960e9f72a4df33f8114ce0ee22b9beefeff50140`

검사는 정적 문서 검사다. 실제 Agent 등록·권한·NAS 조회, 목록 완전성, 데이터의 로컬/클라우드 처리 위치, 라이선스·원본성 승인까지 확인한 결과가 아니다.

## 남은 확인 사항

- Uliya Agent의 실제 등록·권한 및 파일 목록 완전성은 미검증.
- 실제 NAS 실행은 하지 않았다.
- Uliya 처리 위치, SDK 이용 권리, 참가자 최종 승인과 제출 자격은 미해결.
- 본 브랜치는 리뷰용이며 기존 브랜치에 병합하지 않는다.

## 포함 대상

검수 Skill `SKILL.md`, 개인 로컬 경로를 제거한 `G20_P1_OFFICIAL_CHECK_RESULT.json`, 그리고 이 변경·비교 보고서만 공개 브랜치에 추가한다. 공식 도구 원본·SDK 코드·API 키·NAS 자료·비공개 로그는 제외한다.
