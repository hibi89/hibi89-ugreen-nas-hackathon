> **UGREEN 단독 새 채팅 한 문장 (최우선·2026-10-24):** `[유그린 해커톤 깃헙 레포지토리 확인하고 작업하셈]`. 새 대화는 `hibi89/hibi89-ugreen-nas-hackathon`의 **`lead/ugreen` 최신 원격 HEAD**를 조회하고, [현행 START_HERE](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/START_HERE.md) → [최신 LIVE_HANDOFF](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LIVE_HANDOFF.md) → [LIVE_STATE.json](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LIVE_STATE.json) → [LEAD_ACTIVE_WORK](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LEAD_ACTIVE_WORK.md) 순으로 복원해서 **실제 작업부터 이어간다**. 기본 `main`의 과거 요약·`[유그 ...]`·`[해커톤총괄 ...]`은 이 정확한 UGREEN 전용 명령보다 우선하지 않는다. **종료할 때마다** [필수 GitHub 인수인계 절차](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/SESSION_CLOSEOUT.md)를 끝내야 한다.

# UGREEN NAS AI Hackathon — 새 채팅 1문장 시작

사용자가 ChatGPT **새 채팅**에 아래 문장만 남기는 것은 UGREEN 총괄 겸 개발자로서 **저장소 최신 상태를 확인하고 다음 실질 작업을 직접 수행하라**는 지시이다.

```text
[유그 해커톤 깃헙 레포지토리 확인하고 작업하셈]
```

## GitHub 자동 복원 경로

1. 이 저장소 **`hibi89/hibi89-ugreen-nas-hackathon`** 의 최신 GitHub 원격 HEAD 조회.
2. 이 `main` 브랜치는 **진입·안정화된 결과물용**이고 과거 자료가 있다. **현행 실행 기준은 반드시 원격 `lead/ugreen`** 이다. `main`의 구형 '총괄 + 작업자 3명' 안내나 `docs/ROLE_COORDINATION.md`가 최신 업무를 지시한다고 해석하지 않는다.
3. 이동: [lead/ugreen START_HERE](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/START_HERE.md) → [lead HANDOFF](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/HANDOFF.md) → [lead STATUS](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/STATUS.md) → [LEAD_FULLSTACK_PROTOCOL](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LEAD_FULLSTACK_PROTOCOL.md) → **[LEAD_ACTIVE_WORK](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LEAD_ACTIVE_WORK.md)**. 이 순서는 안내용; 상세 필독·승인·기술 검증 순서는 lead START_HERE가 정의한다.
4. 현재 승인된 우선 업무를 **다른 AI 채팅이나 별도 작업자에게 넘기지 않고 총괄 본인이 직접** 수행. 필요할 때 현재 소스·테스트·공식 SDK 근거와 오래된 feature 원본을 검토하며 유료 사용/권한/개인정보/제품 품질 변경은 승인받는다.
5. 중요 작업 후 `lead/ugreen`의 활성 작업·상태·인수인계·상위 보고를 함께 갱신하고 GitHub 원격 커밋 SHA/테스트 근거 확인. 새로운 채팅에 긴 인계 프롬프트를 요구하지 않는다. 사용자가 `ㄱ`을 입력해도 동일하게 다음 실작업을 수행한다.

## 확정 맥락 (스냅샷, 최신 데이터 아님)
- 제품 **ProjectReady NAS**, Uliya 단일 AI Skill. 담당 총괄 = 직접 개발자·테스터·검수자. UGREEN 별도 worker 채팅 없음. 논리 기능은 파일 누락, 버전 충돌, 권한/개인정보 위험.
- 실행 기본 브랜치는 `lead/ugreen`; `feature/missing-files`, `feature/version-conflicts`, `feature/privacy`와 `main`의 기존 작업·데이터는 보존한다.
- 2026-10-24 KST 관측 시 공식 개발 키트의 내부 CLI/Agent 실증 미완료(BLOCKED), 실제 NAS/CI/제출 실증 없음. 새 채팅에서 반드시 재확인.
- 내부 조기 제출 2026-11-10 KST, 공식 예선 마감 **2026-11-16 16:45 KST**, 신규 현금 지출 목표 0원.

### 데이터 신뢰성과 자동 갱신 한계
GitHub를 매번 **직접 읽은 뒤에만** 현재 상태를 확인했다고 말한다. 정적 안내 문서는 시간이 지났다고 자동으로 갱신되지 않는다. 이 프로토콜은 사용자의 새 채팅 명령을 간결하게 만드는 것이며, 백그라운드 개발·정기 자동 실행을 만들지는 않는다.

공개 GitHub에 실 사용자 개인정보, NAS 파일, 토큰, 비공개 다운로드 아카이브, .env 등 올리지 않는다. GitHub 접근 도구가 없다면 그 제한만 사실대로 보고하고, 현재 상태나 성공을 추측하지 않는다.
