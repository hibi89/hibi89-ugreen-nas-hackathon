> **[OWNER-FINAL-BLUEPRINT-100 | 2026-11-13 KST | 사용자 확정·전체 저장소 최우선]** 제품 공식 **최종완성률은 사용자 확정 최종설계도 전체 100%**를 분모로 한다. 총괄·작업자는 임의로 설계를 축소하거나, 해커톤용 MVP·합성 테스트·CI PASS·85/95% 내부 마일스톤을 최종완성률로 혼용할 수 없다. 최종설계 요구사항 ID→코드→정확 SHA 실제 검증→미구현/미검증 및 사용자 승인 가중치를 추적해 계산한다. 근거·가중치가 미비하면 **최종설계 기준 UNASSESSED(재산정 대기)**로 표시하고 종전 수치는 **과거 내부 마일스톤**으로 보존한다. 크몽 관련 완성률은 해총 `kmong-productization` 원장에 동기화한다. [작업중]/등록완료/RELEASE HOLD 등 기존 별도 상태는 보존한다. 상충하는 구형 진척률 산정 지시보다 우선. [공통 전체 규칙](https://github.com/hibi89/hackathon-command-center-2026/blob/kmong-productization/docs/strategy/FINAL_BLUEPRINT_COMPLETION_STANDARD_20261113.md). 정책 커밋은 코드 수정·성공 테스트·제품 출시·재산정 완료를 의미하지 않는다.

> **[KMONG_WORK_TARGET_GATE_20261112 | 사용자 최신 확정 | 필수 작업 규칙]** 이 저장소에서 크몽 상품·육성 후보를 작업하는 모든 AI 담당자는 새 채팅·`ㄱ` 시작 시 이 문구를 읽고 적용한다.
> - 실제 개발/수정/테스트 착수 즉시 [해총 크몽 최종완성률·후보 상태표](https://github.com/hibi89/hackathon-command-center-2026/blob/kmong-productization/docs/audits/KMONG_16_CURRENT_20261111.md)의 **해당 상품명 옆에 `**[작업중]**`을 표시하고 GitHub 커밋**한다. 확정 단계 목표(예: 95%)와 검증 기준을 제품 STATUS/HANDOFF에 남긴다.
> - **목표 완성률 달성 전에는 [작업중]을 삭제하지 않는다.** 일시중단·종료·보류·다른 제품 전환·담당 채팅 변경도 삭제 사유가 아니다. 예전 '전환·중단 시 삭제' 지시는 폐기한다.
> - **검증된 목표치에 도달한 뒤에만** 기능 SHA·PASS/FAIL/SKIP·미검증을 기록하고 자기 표시를 제거·커밋한다. 목표 하향/변경으로 표식 제거 시 사용자 명시 승인 필요. 다른 담당자 표시·기존 수치·RELEASE HOLD 보존.
> - 표식은 목표 미달 상태를 의미하며 **실시간 실행 증명은 아니다**. 허브 최신 HEAD 확인 후 안전하게 반영, 실패 시 `KMONG_HUB_SYNC_PENDING` 기록. 자동 동기화 없음. 크몽 외 작업에는 표시 불필요.

> **2026-10-28 해총 전 저장소 최상위 공통 운영 공지 (소유자 승인):** [개발 가속·로컬검증·병목제거 통합 정본](https://github.com/hibi89/hackathon-command-center-2026/blob/main/docs/DEV_ACCELERATION_AND_VERIFICATION_20261028.md)을 새 채팅 시작 시 먼저 적용한다. **활성 개발 4개 슬롯은 KIC(+Disclosure Lightning)·PayPal·UGREEN·LA만**, 합의된 구현/테스트는 **GPT-6 Instant**, 최초 설계·고위험 난제·해총 독립검수는 높은 추론. 이 저장소의 활성 개발은 각 총괄의 지정 개발 브랜치에 한한다. GitHub 파일별 왕복·중복 문서 갱신을 줄이고, 기능 단위 커밋·실행된 테스트의 SHA/PASS/FAIL/SKIP·단일 안전한 로컬 검증을 우선한다. 이전 지시의 사소한 변경마다 STATUS/HANDOFF/README 전량 갱신 의무보다 본 공통 프로세스를 우선한다. **기존 설계 동결·보안·외부 호출/결제/고객정보·제출 승인 요건은 절대 완화하지 않는다.** 본 문구는 운영 공지이며 기능 검증이나 배포 승인이 아니다.

> **UGREEN 단독 새 채팅 한 문장 (최우선·2026-10-24):** `[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]`. 새 대화는 `hibi89/hibi89-ugreen-nas-hackathon`의 **`lead/ugreen` 최신 원격 HEAD**를 조회하고, [현행 START_HERE](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/START_HERE.md) → [최신 LIVE_HANDOFF](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LIVE_HANDOFF.md) → [LIVE_STATE.json](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LIVE_STATE.json) → [LEAD_ACTIVE_WORK](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LEAD_ACTIVE_WORK.md) 순으로 복원해서 **실제 작업부터 이어간다**. 기본 `main`의 과거 요약·`[유그 ...]`·`[해커톤총괄 ...]`은 이 정확한 UGREEN 전용 명령보다 우선하지 않는다. **종료할 때마다** [필수 GitHub 인수인계 절차](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/SESSION_CLOSEOUT.md)를 끝내야 한다.

> **현행 단일 진입점 (2026-10-24 KST)**: 새 채팅에서 **`[유그 해커톤 깃헙 레포지토리 확인하고 작업하셈]`** 한 문장만 입력하면 [START_HERE.md](START_HERE.md) → 최신 **`lead/ugreen`** [실행 지침](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/START_HERE.md) → [현재 작업](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LEAD_ACTIVE_WORK.md)을 조회하고, UGREEN **총괄 본인이 직접 개발·테스트·검수**한다. **아래 기능별 AI 작업자 3명/디스패처 문구는 폐기된 과거 이력이다.** `main`은 기본 진입·검증된 통합 기준이며 최신 진행은 lead 브랜치가 권위 있다.

# UGREEN AI 역할 및 공통 운영 규칙

- 실제 참가자: 사용자 **1명**. AI 담당자들은 각자 독립 대화와 GitHub 브랜치에서 작업한다.
- 대회 총괄(`lead/ugreen`)이 제출·아키텍처·검수·통합·개발 지시 책임을 진다. 기능 담당자는 `feature/missing-files`, `feature/version-conflicts`, `feature/privacy`만 수정한다. 최상위 해커톤 총괄은 전체 일정·위험·공식 성과만 감독한다.
- 다른 브랜치의 소스/메시지/기능은 사용자 승인 없이 수정하지 않는다. `main`은 검증된 통합 기준이다.
- 시작: **자기 브랜치** `HANDOFF.md` → `STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → 역할별 `docs/roles/<role>/OPERATIONS.md`. 최신 GitHub HEAD·실제 소스와 대조한다.
- 작업 종료: 기능/실행/테스트/실패·검증·미검증 구분 → `STATUS`·`HANDOFF`와 메시지함/상위 보고 갱신 → 자기 브랜치에 커밋, 원격 SHA 검증. 단순 질의에는 불필요한 커밋 금지.
- 총괄은 새로운 기능 지시 전에 세 기능 브랜치의 최신 `TO_UGREEN_LEAD.md`를 전수 확인하고 `MESSAGE_REVIEW.md`에 기록한다. 채팅 간 자동 전송·실시간 동기화 없음.
- 원본·기존 정상 기능·데이터 보존. 설계 2안 비교 후 사용자 승인. 유료 API/결제·개인정보 외부 전송·권한/공개 설정 변경·기존 원본 변경은 승인 필요.
- 토큰·.env·비밀번호·개인정보·비공개 원본 업로드 금지(**저장소 Public**). API Sandbox 성공/합성 테스트/CI/Production 실제 동작을 구분한다.
- 이 운영 문서는 코드 개발 완성의 근거가 아니다. 대회 공식 규정은 https://ugreenhackathon.devpost.com/rules.

## 검수 후 확정된 시작 경로 (2026-10-24 KST)
- `main`에서 [ROLE_COORDINATION.md](docs/ROLE_COORDINATION.md)로 각 AI 역할 브랜치를 찾는다. **main에는 역할별 HANDOFF/STATUS가 없으므로** 총괄/작업자 채팅은 반드시 자신의 소유 브랜치 `docs/roles/<role>/HANDOFF.md`부터 읽는다.
- 로컬 코드가 아직 없어 자동 테스트/CI는 미설정이다. 이 사실을 '테스트 성공'이라 기록하지 않는다. 추후 코드 개발 시 최소 테스트·CI·API/브라우저 검증 계약을 대회 총괄이 정한다.
