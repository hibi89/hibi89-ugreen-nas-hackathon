> **[G21 2026-10-24 — 리뷰 브랜치 P1 보완 실파일 독립검수 완료 / 제출 패키징 미완성](docs/submission/G21_P1_REMOTE_BRANCH_INDEPENDENT_AUDIT_20261024.md)**: `review/ugreen-official-creator@7af2cb750b37826fb02a00e2d45cb73f3a85c239`의 실제 Skill 10,481B SHA256 `164e84fe2fd8bc14e421b5469cc862aa4971f71c9b46aea08cc2f281c7229ead` **원격 바이트로 독립 검증**. checker JSON SHA `92a6891b0889a89cd09f16ed960e9f72a4df33f8114ce0ee22b9beefeff50140` **독립 검증**, 내용 `static-pass` 0오류/0경고(실 checker 호출은 Codex 보고). **위임 문맥 누락 P1 수정은 본문 검수 PASS.** 단 **신규 1파일 Skill은 참조 링크 0개인데 브랜치 내 구형 `references/*.md` 3개가 남아 기존 4파일 빌드/감사 규격과 불일치**. 별도 깨끗한 단일파일 패키징/권리고지 및 Q8 PDF 정정 필요; 원본 `lead/ugreen` Skill 불변, 승인/Devpost/NAS 미완료. 총괄은 이 이슈 해결 전 제출 적격성 완결 선언 금지.

> **[G20 2026-10-24 20:51 KST 검수 ZIP 실물 독립검증](docs/submission/G20_UPLOADED_REVIEW_ZIP_INDEPENDENT_AUDIT_20261024.md)**: 참가자가 직접 업로드한 실제 `ProjectReady_OFFICIAL_REVIEW.zip`과 3개 포함 파일의 SHA256/ZIP 안전성 모두 일치. 신규 `projectready-nas/SKILL.md` 7,345B SHA256 `e1b071666b836cc464147821d7823bc3061c757434697d9a64250d4a9abd5b4a` **독립 확인**. 첨부 공식 checker JSON은 `static-pass` 오류0/경고0이며 대상 파일 SHA 일치(실제 checker 실행 자체는 Codex 보고). **보완 P1:** 하위 expert delegate 명령에 실제 승인 폴더/필수 체크리스트/후보 패턴·승인된 파일 참조/질문 값을 삽입해 **자기완결형 위임 지시**가 되도록 명확히 구현한 뒤 공식 검사 재실행. 예선 PDF Q8의 '공식 validator 미실행' 표현도 새 후보 적용 시 정정. 검수용 ZIP ≠ Devpost 제출 ZIP. 실 NAS·Agent·권리 승인·최종 제출은 아직 미완료, 기존 GitHub Skill 불변.

> **[G18 2026-10-24 20:23 KST — 참가자 Codex의 공식 UGOS Creator 실생성·static-pass 보고 접수](docs/submission/G18_CODEX_CREATOR_RESULT_REPORTED_20261024.md)**: 신규 ProjectReady NAS `SKILL.md` 생성 SHA256 `e1b071666b836cc464147821d7823bc3061c757434697d9a64250d4a9abd5b4a`, 필수 제목 수정 후 공식 정적 checker `static-pass` 오류 0/경고 0이라는 **사용자 전달 Codex 보고**. 새 파일 실물은 GitHub에 없으므로 파일 해시·본문/참조·권리·보안 **독립 검수 미완료**. NAS/실 Agent 미실행, 원본 Skill 불변, 최종 PDF/ZIP 승인·Devpost·SkillHub 게시 미실시. 다음 최우선: 생성된 `SKILL.md`와 직접 참조 Markdown 수신 후 검수. MASTER 상태는 증거 수신까지 보수적으로 유지.

> **[2026-10-24 공식 대회 규정/참가/도구/일정 신규 공시 — 통합 해커톤 총괄 필독](docs/contest/UGREEN_OFFICIAL_BRIEF_20261024.md)**: 공식 [Rules](https://ugreenhackathon.devpost.com/rules)·[Resources](https://ugreenhackathon.devpost.com/resources)·[Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) 직접 대조. 예선 마감 **11/16 16:45 KST**, PDF 10문항/500단어 + 초기 Skill ZIP ≤10MB, 공식 UGOS Creator 실생성 필요. 사용자 보고 기준 PC 설치/재시작 Codex Skill 인식은 확인됐으나 **실제 공식 생성/검사 완료 결과는 아직 미접수**. 전체 진도/CI 정본은 MASTER_PROGRESS와 실제 최신 HEAD를 읽을 것. 사용자 승인·Devpost 제출 전제 금지.

> **2026-10-24 최신 우선 규칙:** [MASTER_PROGRESS.md](MASTER_PROGRESS.md) = 날짜별 24건의 DONE/PARTIAL/BLOCKED/NOT_STARTED·선행 작업·테스트 증거·기본/별도 예비시간에 관한 **최신 진행 정본**. `lead/ugreen` 원격 HEAD 확인 후 이 문서를 **가장 먼저 읽고**, 이후 LIVE_HANDOFF/LIVE_STATE와 증거를 대조한다. **작업을 끝낼 때마다 MASTER를 포함한 필수 인수인계 파일을 같은 push로 갱신**하고 GitHub Actions 진행표 무결성 검사를 통과해야 한다. 아래 구형 읽기 순서는 MASTER 우선 원칙에 따라 해석한다.

# UGREEN — 한 문장 복원 (2026-10-24 KST 최신 규칙)

**사용자 명령(그대로 입력):** `[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]`

이 문장을 받은 새 ChatGPT 대화는 **UGREEN NAS AI Hackathon의 단일 총괄 겸 직접 개발자**로 복원한다. 긴 인수인계 프롬프트·채팅 기록·사용자 재설명은 요구하지 않는다. GitHub의 **`hibi89/hibi89-ugreen-nas-hackathon` 저장소 `lead/ugreen` 최신 원격 HEAD**가 작업 상태의 정본이며, `main`·옛 feature 브랜치·오래된 문서의 과거 상태를 현재 지시로 사용하지 않는다.

## 새 채팅 실행 순서 (추가 확인 질문 없이)
1. GitHub 연결 도구로 `lead/ugreen`의 **현재 원격 HEAD SHA**를 가져온다. 연결이 실패하면 접근 차단 사실만 설명하며 임의로 진행 상황을 만들지 않는다.
2. **반드시 이 순서로 최신 버전 읽기**: [`docs/roles/lead/LIVE_HANDOFF.md`](docs/roles/lead/LIVE_HANDOFF.md) → [`docs/roles/lead/LIVE_STATE.json`](docs/roles/lead/LIVE_STATE.json) → [`docs/roles/lead/LEAD_ACTIVE_WORK.md`](docs/roles/lead/LEAD_ACTIVE_WORK.md) → [`docs/roles/lead/DAILY_PROGRESS.md`](docs/roles/lead/DAILY_PROGRESS.md) 및 `DAILY_PROGRESS.json` → [`docs/roles/lead/CARRYOVER_TASK_SCHEDULE_20261024.md`](docs/roles/lead/CARRYOVER_TASK_SCHEDULE_20261024.md) → [`docs/WORK_ORDER_FLEX_POLICY_20261024.md`](docs/WORK_ORDER_FLEX_POLICY_20261024.md) → 해당 소스·테스트·CI 증거.
3. [`docs/roles/lead/SESSION_CLOSEOUT.md`](docs/roles/lead/SESSION_CLOSEOUT.md)의 **종료/인수인계 필수 절차**를 읽는다. 완료·미완료·차단·실측시간·예비시간 및 기존 선행 개발 중복 여부를 검증한다.
4. 사용자의 '작업하셈'은 **실제로 조사/구현/테스트/검수/원격 커밋**하라는 뜻. 단순 복원 보고서만 작성하지 않는다. 현재 READY하고 독립 검증 가능한 최우선 업무를 바로 수행하며, G1 SDK 차단은 해결됐다는 증거가 있을 때만 해제한다. G2/G3b/G3c/G4/G5의 이미 합성 검증된 코드는 재구현하지 않는다.
5. **작업이 끝날 때마다** LIVE_HANDOFF, LIVE_STATE, LEAD_ACTIVE_WORK, DAILY_PROGRESS(.md/.json), STATUS, HANDOFF, TO_HACKATHON_LEAD, WORK_TIME_LOG, 날짜별 이월표를 필요한 범위에서 모두 동기화하고 **같은 `lead/ugreen` 브랜치에 커밋/푸시**, 원격 SHA 및 CI 상태 재조회 후 종료 보고한다. 새 사용자 메시지 없이 백그라운드로 개발하는 기능은 아니다.

**2026-10-24 기준:** 해당 날짜에 수행한 실제 산출물 **100% 완료/남은 0h**(실제 경과시간 미측정), 오프라인 합성 CI [91/91 PASS](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40066651248). **G1 공식 SDK CLI/Expert Agent/권한/라이선스 내부 명세 및 NAS 실제 실행은 미검증·BLOCKED**. 다음 예정 G1 업무 **10/25 계획 1.5h+별도 예비 1.5h, 실제 완료 ETA 미정**. 전체 작품 제출/본선 진출로 혼동하지 않는다.

**대회 마감:** 예선 공식 2026-11-16 **16:45 KST**, 내부 조기 제출 11/10 조건부, 비용 신규 0원. 사용자 폴더의 외부 전송/삭제/유료 결제/공식 SDK에 없는 명령은 임의 수행하지 않는다.

## 정본/이력 우선순위
사용자 최신 지시 → **`lead/ugreen` 현재 원격 소스·테스트/CI** → `LIVE_HANDOFF.md` + `LIVE_STATE.json` → `LEAD_ACTIVE_WORK.md` → 날짜별 공시 → 과거 회의록/옛 UGR dispatcher·worker 문서. 구형 `[유그 ...]`·`[해커톤총괄 ...]`는 **과거 별칭이고 사용자에게 권장하지 않는다**.
