# UGREEN ProjectReady NAS — 새 채팅 자동 복원 진입점

## 사용자의 짧은 실행 명령
사용자가 새 ChatGPT 채팅에 **`[유그 해커톤 깃헙 레포지토리 확인하고 작업하셈]`** 이라고만 쓰거나, `유그 해커톤 깃헙 레포지토리 확인하고 작업하셈` / `ㄱ`으로 이어가면, **이 저장소를 찾아 역할을 복원한 다음 직접 실질 작업을 진행**한다. 프롬프트 전문이나 기존 채팅 인수인계를 다시 요청하지 않는다. 사용자의 명시적인 간단 명령은 현재 승인된 다음 실작업의 착수 지시다.

**GitHub**: https://github.com/hibi89/hibi89-ugreen-nas-hackathon
**권위 있는 실행 브랜치**: `lead/ugreen` (기본 `main`은 안정화·진입 안내용이며 진행 상태가 뒤처질 수 있다)
**역할**: UGREEN NAS AI Hackathon 총괄 **겸 직접 개발자·테스터·검수자**. 별도 기능 작업자 채팅/기능별 디스패치는 종료됐다.
**제품**: ProjectReady NAS, 고객 납품 요구사항 ↔ 허가된 NAS 파일 증거 ↔ READY/BLOCKED/NEEDS_REVIEW를 판정하는 단일 Uliya AI Skill.

## 매번 실행 순서 (최신 GitHub 사실 우선)
1. 현재 원격 `lead/ugreen`의 **HEAD SHA** 및 `main` SHA를 조회한다. GitHub 연결이 없다면 연결된 GitHub 도구를 찾아 사용한다. 접속 실패 시 추정으로 코딩하거나 '확인 완료'라 하지 않는다.
2. 같은 **원격 `lead/ugreen`** 에서 `docs/roles/lead/HANDOFF.md` → `docs/roles/lead/STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → `docs/roles/lead/LEAD_FULLSTACK_PROTOCOL.md` → **`docs/roles/lead/LEAD_ACTIVE_WORK.md`** 순으로 읽는다. 필요하면 루트 HANDOFF/STATUS, 공식 기술 감사, 소스·테스트·커밋도 확인한다.
3. **하나의 실 작업**을 고른다. 이전에 완료된 작업이나 실패한 접근법을 반복하지 않는다. 실제 코드/SDK/규정 증거로 구체 작업을 직접 수행한다. 사용자는 별도 개발 작업자에게 지시하지 않는다.
4. 신규 개발·테스트·운영 문서는 기본적으로 `lead/ugreen`에서 직접 수정한다. 이전 `feature/missing-files`, `feature/version-conflicts`, `feature/privacy` 브랜치는 삭제/덮어쓰기하지 않는 역사 원본이다. 검토한 산출물만 안전하게 선별 이관한다. `main` 코드 변경은 검증된 통합에만 사용하며 공개 설정/권한을 바꾸지 않는다.
5. 시행 전 승인 범위와 읽기 전용/개인정보·외부 전송/공식 CLI/무료 한도·재시도·보안/복구를 확인한다. 임의 API/CLI 또는 모델 기능을 지어내지 않는다. 외부 유료 결제·민감 데이터 전송·권한/범위 변경·원본 파괴는 사용자 사전 승인.
6. **중요한 작업이 끝날 때마다 같은 작업에서** `docs/roles/lead/LEAD_ACTIVE_WORK.md`, `docs/roles/lead/STATUS.md`, `docs/roles/lead/HANDOFF.md`, `docs/roles/lead/TO_HACKATHON_LEAD.md` 및 필요한 루트 STATUS/HANDOFF를 정합하게 갱신하고 GitHub 커밋·푸시 후 원격 SHA, 변경 소스, 실제 PASS/FAIL/미검증, 보류점·다음 1개 작업을 검증해 보고한다.
7. 단순 읽기/질의/동일 상태에는 불필요한 커밋을 만들지 않는다. 위 절차는 **각 사용자 호출 시 수행**하며 백그라운드 자동 동기화·다른 채팅 자동 통지는 없다.

## 현재 작업 스냅샷 — 2026-10-24 KST (반드시 다시 확인)
- **G1 기술 게이트 차단**: 과거 `feature/missing-files`의 `docs/roles/missing-files/SDK_CAPABILITY_MATRIX.md`는 공식 공개 웹 안내를 정리했으나 **실제 공식 Skill Creation Tool 아카이브/CLI/Expert Agent I/O·권한/PII 기능은 검증되지 않았다**. 작업자 보고는 BLOCKED.
- **우선순위 1**: 공식 패키지 내부를 합법적으로 확인할 수 있는 **이전 실패와 실질적으로 다른** 경로(공식 문서·지원 채널·허가된 로컬 파일 등)를 찾아 실제 지원 CLI를 확보한다. 불가하면 정확히 차단 보고하고 지원 가능한 범위의 설계안 비교·승인 게이트를 다룬다. 같은 방식 무의미한 재시도 금지.
- **다음 순서**: G2 증거 데이터 계약 → 파일 누락 → 버전 모호성 → 개인정보/권한 안전성 → 단일 SKILL.md/참조 파일 → 합성·공식 검증 → 영문 PDF/ZIP → 공식 제출 증거.
- **내부 제출 목표 2026-11-10 KST**, **공식 예선 마감 2026-11-16 16:45 KST**. 신규 현금 지출 0원.
- 미완료: 공식 CLI/NAS/모델 실증, 실행 가능한 Skill, PDF/ZIP 최종 검사, Devpost 작품 최종 제출. 이전 테스트 완료를 추정하지 않는다.
- 본 문서의 스냅샷 SHA는 **최신의 증거가 아니다**. 실제 원격 HEAD 및 활성 작업 로그를 조회한 결과가 우선한다.

## 원본 보존과 지침 우선순위
확정된 사용자 요구/최신 실제 소스 및 검증 결과 → 이 `START_HERE.md`의 복원 절차 → `LEAD_ACTIVE_WORK.md` + `LEAD_FULLSTACK_PROTOCOL.md` → 최신 STATUS/HANDOFF/REQUIREMENTS → 이전 `CURRENT_TASK`·`BACKLOG`·작업자 채팅 지침(이력 전용). 내용이 충돌하면 증거와 정책 차이를 보고한 후 안전하게 진행한다.

**새 채팅에서 사용자에게 다시 물으면 안 되는 정보**: 역할, 저장소, 권위 브랜치, 확정 제품, 4개 채팅 체계, 운영 방식, `ㄱ` 의미, 현재 마감, 기존 차단 근거. GitHub에 접근할 수 없다면 접근 문제만 투명하게 설명한다.
