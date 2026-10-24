# UGREEN Hackathon 2026 — 공식 대회 정보 정본 (2026-10-24 KST 검증)

> **대회 총괄 및 신규 UGREEN 담당자 필독.** 이 페이지는 UGREEN 공식 Devpost Rules / Resources 및 Starter Kit을 기준으로 한 **날짜 고정 스냅샷**이다. 참가 자격·마감·파일 형식은 [공식 Rules](https://ugreenhackathon.devpost.com/rules)가 우선하며 변경될 수 있다. GitHub에 작성했다고 Devpost에 등록·제출한 것은 아니다. 사용자 입력 없이 자동 재확인하거나 백그라운드 작업을 수행하지 않는다.

## 1. 대회 식별 및 필수 링크

- 공식 명칭: **UGREEN Hackathon 2026 on AI NAS — Bring Your Skills to UGOS**.
- [대회 메인/참가 신청](https://ugreenhackathon.devpost.com/) · [공식 규정 (우선 원문)](https://ugreenhackathon.devpost.com/rules) · [공식 개발 리소스/FAQ](https://ugreenhackathon.devpost.com/resources) · [UGREEN 공식 Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit).
- [UGREEN UGOS](https://ai.ugreen.com/pages/operating-system) · [UGREEN Skills Hub](https://skills.ugreen.com/skill-hub/) · [공식 UGREEN NAS 커뮤니티](https://community.ugreen.com/). 공식 Resources에는 기술 지원 주소 `nas-support@ugreen.com` 및 별도 지원 티켓 링크가 있다. 실제 문의 발송은 **NOT_SENT**.
- 목표: UGREEN AI NAS에서 작동하는 **공식 Uliya 표준의 AI Skill**. 선택 트랙은 *Automate Your Workflow / Bring Memories to Life / Unleash Your Creativity / Open Innovation* 중 하나. 현재 ProjectReady NAS는 작업 자동화와 연관이 있으나 **제출 트랙 선택·확정은 아직 사용자/Devpost 확인 전**.
- 참가: 법적 성년 개인, 최대 3명 팀. 대한민국은 공식 참가 가능 지역에 포함된다. 개인 참가자는 팀 참가와 중복할 수 없다. **우리 Devpost 참가 신청 및 최종 제출 영수증은 아직 확인되지 않았다**. 실제 접수 상태를 추측하지 않는다.

## 2. 일정 — 미국 시간과 한국시간 혼동 금지

| 단계 | 공식 미국 Pacific Time (PT) | 한국시간 KST (계산 변환) |
|---|---|---|
| 등록 및 예선 Round 1 마감 | **2026-11-15 일 23:45 PST** | **2026-11-16 월 16:45 KST** |
| 예선 심사 | 2026-11-16~19 PT | 공고 미국 현지 일정 참조 |
| 본선 초청 예정 | **2026-11-21 토 00:00 PST** | **2026-11-21 토 17:00 KST** |
| 본선 NAS 실기 검증 배정일 | 2026-11-22~28 PT 중 **1일** | 배정 통지 이메일의 실제 시간 우선 |
| 본선 Round 2 최종 제출 마감 | **2026-11-30 월 23:45 PST** | **2026-12-01 화 16:45 KST** |
| 수상 발표 예정 | 2026-12-06 일 14:00 PST 전후 | **2026-12-07 월 07:00 KST 전후** |

- 미국 PT는 계절별 시간대를 포함한다. 위 11~12월 마감 변환은 **PST (UTC-8) → KST (UTC+9), 시차 +17시간** 적용. Devpost의 "11월 15일까지"와 한국의 "11월 16일 16:45"는 **동일한 순간**이다.
- 내부 조기 제출 목표 11/10 또는 11/14는 **공식 마감이 아니다**. 시간 변동 가능성이 있으면 [Rules](https://ugreenhackathon.devpost.com/rules) 최신 값을 재확인한다.
- Round 1에서 **최대 30개 프로젝트만 본선 진출**. 초청은 공식 이메일/Devpost 확인 전까지 `NOT_CONFIRMED`.
- 본선 진출팀에게는 UGREEN **iDX6011 Pro 64GB AI NAS** 원격 접근을 지정된 **하루(미국 PT 기준)** 무료 제공; 별도로 기기를 구매하거나 NAS 접근을 신청할 필요 없다. 계정/테스트일은 UGREEN 통지 기준.
- 총상금 **$46,000 USD**: Gold $20k(1), Silver $10k(1), Bronze $6k(1), Most Creative $5k(2). 각 프로젝트는 **상금 한 개만 수상**.

## 3. Round 1 — 제출의 필수 조건과 불필요한 것

**필수**
1. 공식 [UGOS Skill Creation Tool](https://ai.ugreen.com/pages/hackathon-starter-kit)을 실제 사용해 **신규 Uliya Skill 생성**. 도구는 Codex / Claude / WorkBuddy 지원. 기존 자체 작성 SKILL.md, 공개 API 카탈로그 조사, 일반 Python 합성 테스트만으로는 공식 도구 **실생성**을 입증하지 못한다.
2. **영문 PDF**: 공식 Rules의 **10개 질문에 대한 실질 답변 합계 최대 500 English words**. 이름·서명·팀 동의·서드파티 라이선스 설명은 이 실질 답변 제한에서 제외된다는 것이 공식 규정. 우리 내부 PDF **1MB 상한은 보수적 자체 QA**이며, Rules의 명시 상한으로 단정하지 않는다.
3. **초기 Skill ZIP 10MB 이하**: 루트 Skill 진입점 `SKILL.md` 필수, 하이픈을 사용하는 소문자 `name`(2~64글자), `description`(최대 1024글자), 필요한 경우 `references/*.md`를 `SKILL.md`에서 직접 링크. 공개 SDK 소스나 독립 실행 스크립트·바이너리·별도 매니페스트·비밀키 포함 금지.
4. 공식 Uliya Skill 개발 표준 준수, **등록된 Expert Agent와 지원되는 UGOS CLI**만 사용. 불명확한 명령·특권 NAS 접근·근거 없는 파일 목록 완전성 주장 금지.
5. 참가자 본인/팀 원작품, 제3자 권리·라이선스·AI 보조 도구 및 외부 서비스/데이터 흐름 고지, 제출 파일 실제 확인과 **명시적 사용자 승인**. 제3자 비공개 자료, 실제 개인정보, 고객 NAS 경로·키 등 공개/업로드 금지. 모든 공식 제출 자료와 대회 커뮤니케이션은 영어.

**Round 1 필수 아님**
- 실제 UGREEN NAS 보유·원격 테스트·실기 동작 검증 / 실동작 영상 / 런타임 스크린샷 / 공개 GitHub 주소 / 소스 저장소 이력 / 로컬 테스트 보고서. 최종 심사에서는 본선 실제 동작 검증 필요.
- Starter Kit이 권장하는 **공식 제작 도구의 Check/review**는 실행하고 결과를 보존할 것. 단, Round 1에 NAS 실제 설치/운영은 필수라고 혼동하면 안 된다.

## 4. Round 2 — 진출 조건부

- 동일한 ProjectReady NAS Skill을 실제 배정된 UGREEN NAS에 설치·실행·오류 수정·시연. 시험 장비/접속 정보는 공개 GitHub에 절대 저장하지 않는다.
- **최종 Skill ZIP**과 **공개 YouTube 시연 영상(3분 미만 권고/판정 기준)** 제출. NAS에서 실제 실행하는 영상, 영어 음성 또는 완전한 영어 자막 필수. 저작권·브랜드·음원·개인정보 검수.
- Round 1 점수는 Round 2 수상 결정으로 **이월되지 않음**.

## 5. 심사 기준 (각 25% 동일 가중치)

1. **User Value**: 실제 사용자 문제, 흐름과 유용한 결과.
2. **Innovation & Differentiation**: 기존 범용 AI와 다른 실질 기능·작업 흐름.
3. **Technical Quality**: 등록된 Agent·CLI 사용, 권한·실패 처리·작업 연결·신뢰성.
4. **AI NAS Fit & Validation**: NAS 저장소/로컬 데이터·개인정보·지원 기능의 의미 있는 활용과 검증 설계.

**우리 ProjectReady NAS에서 강조할 것:** 사용자 승인 폴더 내 필수 납품물 점검, 완전한 조회에만 MISSING, 미완전/접근 거부는 NOT_CHECKED, 판본 충돌은 사람 검토, 무단 NAS 수정/대외 전송 없음. 이는 **기획 및 합성 검증** 근거이지 공식 NAS 실검증 증거가 아니다.

## 6. 현재 구현/참가 증거 — 작업자 보고와 독립 검증 분리

- GitHub 정본: [UGREEN lead/ugreen](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/tree/lead/ugreen) / [24일 마스터](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/MASTER_PROGRESS.md) / [G12 공식 Creator 런북](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/submission/G12_OFFICIAL_CREATOR_CODEX_RUNBOOK.md).
- **검증된 원격 CI:** 기존 오프라인 합성 211/211 PASS; 최신 PDF·Skill ZIP DRAFT 빌드/무결성 [Actions 40087085326](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40087085326) SUCCESS. **DRAFT_NOT_APPROVED / NOT_SUBMITTED**.
- **사용자 전달 Codex 실행 결과(사용자 보고, GitHub에서 독립 검증한 것은 아님):** 공식 v0.7.3 제작 도구 ZIP SHA256 `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3`, 참가자 PC의 Codex Skill 설치 성공 `CODEX_SKILL_FOLDER_COPIED_ONLY`; 재시작 후 Codex에서 `uliya-skill-kit` 인식되고 공식 생성 워크플로 착수했다는 화면 확인. 사용자 개인 Windows 경로는 공개하지 않는다.
- **확인되지 않은 결과:** 공식 제작 도구가 **실제로 신규 Skill 파일을 생성·검사 완료했는지**, 결과 파일 SHA/검사 상태/원작품 및 저작권 최종 검수. `OFFICIAL_CREATOR_GENERATION_PENDING_EVIDENCE`; `CHECKER_NOT_EVIDENCED`; NAS/실 Expert Agent 운영 `NOT_RUN`; 권리/입력자료 라이선스 승인 `PENDING`; 실제 Devpost 제출 `NOT_SUBMITTED`.
- **다음 P0:** 사용자 제공 Codex 최종 결과를 받은 뒤, 공식 도구의 실생성 provenance/검사 내용 확인 → 승인된 내용만 기존 Skill에 안전 통합 → 제출 PDF·ZIP 다시 빌드·SHA 검수 → 사용자 명시 승인 → Devpost 실제 접수/영수증 확인. 승인 전 자동 제출 금지.
- 기존 24일 작업일 상태 **DONE 2 / PARTIAL 12 / BLOCKED 3 / NOT_STARTED 7**는 실생성 증거가 나오기 전 변경하지 않는다. 데일리 배정 100%와 전체 프로젝트 완성률 혼동 금지.

## 7. 공식 출처 (2026-10-24 KST 확인)

- [Rules — §1 Dates; §3 Eligibility; §4 Project/Round1/2; §6 Judging; §8 Prizes](https://ugreenhackathon.devpost.com/rules)
- [Resources — 공식 패키지/FAQ/지원/NAS 본선 배정](https://ugreenhackathon.devpost.com/resources)
- [Starter Kit — §1 약관, §2 지원 assistant, §3 설치, §4 feasibility, §5 생성, §7 검사](https://ai.ugreen.com/pages/hackathon-starter-kit)
- [공식 사용자 약관](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-user-agreement) · [개인정보 보호](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-privacy-policy) · [Skill 게시/안전 규칙](https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-publish-audit-spec).
