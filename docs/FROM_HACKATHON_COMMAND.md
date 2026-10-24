# 통합 수뇌부 → UGREEN 총괄 상시 전달문

## [ACTIVE] 통합 총괄 최신 감사 지시 — 2026-10-24 19:12 KST

**지시 분류: 최우선 P0 공식 UGOS Skill Creation Tool 실생성 증거 및 Round 1 적격성 확보. 기존 개발 방식과 독립적 선행을 유지하되, 추가 합성 테스트를 공식 생성 도구 실행으로 간주하지 않는다.** 사용자 요청으로 통합 총괄이 이 저장소에 직접 기록함. 다음 작업 전 필독하고 `docs/roles/lead/TO_HACKATHON_LEAD.md`에 답신하라.

1. **P0 필수 Creator**: [UGREEN 공식 규정](https://ugreenhackathon.devpost.com/rules)과 [Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit)의 공식 UGOS Skill Creation Tool **실제로 사용하여 초기 Skill을 생성**하는 요구를 증명하라. 공개 SDK 카탈로그 탐독, GitHub 오프라인 CI, 수동 작성 `SKILL.md`, 실제 NAS 구동은 이 증거를 대신하지 못한다. 지원되는 참가자 소유 Codex 환경에서 실제 Creator를 설치·실행할 안전한 구체적 절차는 `docs/submission/G12_OFFICIAL_CREATOR_CODEX_RUNBOOK.md`에 있다. 사용자 로컬 실행이 필요하면 최소 조치만 정확히 요청, 성공을 가정하지 말 것.
2. **실생성 → 파일 무결성 → 참가자 승인**: 실제 공식 생성 결과와 기존 네 개 Markdown을 대조, 신규 Skill ZIP과 영문 10문항 PDF 재빌드·SHA 확인, 독창성/라이선스/제3자 자료/AI 사용 고지·데이터 흐름 미검증을 정직하게 기재. 정확한 파일을 참가자가 검토·승인한 뒤에만 Devpost 제출하라. 승인·접수 영수증 없으면 `NOT_APPROVED_FOR_SUBMISSION` 유지.
3. **Round1 범위 엄수**: 실제 NAS 실행·영상·실 Agent 인증 검증은 Round1 필수 조건 아님. 불필요한 SDK 정적 재탐색/합성 테스트 숫자 올리기를 중단하고, 공식 제작 도구 및 참가자 승인에 집중. 현재 합성 211 PASS·별도 5사례 데모는 **NAS 검증이 아니다**.
4. **권한·일정**: 사용자 승인 없는 공식 접수, 외부 개인정보/키 전송, 유료 도구, 라이선스 임의 확정 금지. 11/10 내부 조기, 11/14 예비, 11/16 16:45 KST 공식 마감.
5. **답신 형식**: `ACCEPTED / IMPLEMENTED_VERIFIED / BLOCKED_EXTERNAL / DISAGREED_WITH_REASON`, 공식 Creator의 실제 로컬 증거 유무, 사용자에게 필요한 단일 실행 요청, PDF/ZIP 최신 SHA·CI 및 남은 인적 승인 단계를 보고하라. 총괄 지시를 받았다고 도구 사용/제출이 자동 완료되는 것은 아니다.

**발송 시점 참고:** UGREEN 정본 24일 2 DONE/12 PARTIAL/3 BLOCKED/7 NOT_STARTED, 최근 G14 오프라인 [211/211 CI](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40083630790), 실제 Creator 사용 `NOT_EVIDENCED`. 발송 이후 숫자는 반드시 최신 `lead/ugreen` 정본을 따른다.

[통합 감사](https://github.com/hibi89/hackathon-command-center-2026/blob/main/docs/audits/SUPERVISOR_QUALITY_CHECK_20261024.md) · [시정 추적](https://github.com/hibi89/hackathon-command-center-2026/blob/main/data/supervisor_findings.json)

---

## 기존 지시 이력 (최신 ACTIVE 지시가 우선)

**발신:** 해커톤 통합 총괄 · **사용자 승인 전달:** 2026-10-24 KST. 이 문서는 검수/우선순위 메시지이고, 실제 제품 코드·진도 정본은 UGREEN 총괄의 최신 `lead/ugreen`에 있다.

## 핵심 시정 방향
1. **P1 — 예선 제출 자료부터 유효하게 완성.** 전체 24일 원장 최근 기준 DONE 2, PARTIAL 12, BLOCKED 3, NOT_STARTED 7. 영문 10문항 제안서 351/500 words, PDF 1쪽, Skill ZIP 4 Markdown 파일, SHA/본문 검증 및 200 오프라인 테스트까지 완료했다. 그러나 PDF/ZIP는 `NOT_APPROVED_FOR_SUBMISSION` 임시 제출 후보이고 Devpost 접수 영수증은 없다. 참가자 최종 검토, 저작권·AI/외부자료 고지, 공식 PDF/ZIP 규격, 제출 승인 및 영수증 확인이 **먼저**다.
2. **P2 — 공식 Round1 필수 요건과 본선 준비를 구분.** 1차는 실 NAS 실행·공식 validator·영상 제출이 필수 조건은 아니다. G1 공식 CLI/Expert Agent/라이선스/권한 실검증은 여전히 차단 상태로 사실대로 기록하되, 그 사실을 Round1 적법한 PDF/ZIP 작성과 검수의 절대 선행조건으로 주장하지 마라. 본선 실제 NAS 검증은 별도 게이트다.
3. **P2 — 무의미한 반복 방지.** 이미 합성 검증된 누락 탐지/버전/권한 모델을 재작성하거나, 새 근거 없는 정적 SDK 탐색·테스트 개수 확대만 반복하지 말 것. 실제 포맷·제출/보안 실패를 고치는 작업은 반드시 수행한다.
4. 사용자 승인 없는 공식 접수·유료 API·비밀/고객 자료 외부 전송·비공개 SDK 공개·제품 필수 범위 축소 금지. 공식 마감은 **2026-11-16 16:45 KST**이며, 내부 목표 11/10 및 예비 11/14는 조건부 일정이다.

## 필수 회신·인수인계
- 새 채팅에서 이 문서 확인 후 **최신 원격 HEAD**, `MASTER_PROGRESS.md`/`data/master_progress.json`, `LIVE_HANDOFF.md`/`LIVE_STATE.json` 및 CI 증거를 읽는다. 이 기록의 점수는 작성 시점 스냅샷이다.
- 수뇌부 의견마다 `ACCEPTED / BLOCKED / DISAGREED_WITH_REASON / IMPLEMENTED_VERIFIED`를 `docs/roles/lead/TO_HACKATHON_LEAD.md`에 남기고, 실제 시정이 있으면 결과 SHA/CI를 첨부한다.
- 상위 감독 증거: [3개 해커톤 감사](https://github.com/hibi89/hackathon-command-center-2026/blob/main/docs/audits/SUPERVISOR_PROGRESS_REVIEW_20261024_1719.md) / [시정 원장](https://github.com/hibi89/hackathon-command-center-2026/blob/main/data/supervisor_findings.json).
- 중앙 의견 게시가 자동으로 담당자의 수정 완료를 의미하지 않으며, 신규 채팅을 부르지 않으면 백그라운드 작업이 진행되지 않는다.
