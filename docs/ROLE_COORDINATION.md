> **현행 단일 진입점 (2026-10-24 KST)**: 새 채팅에서 **`[유그 해커톤 깃헙 레포지토리 확인하고 작업하셈]`** 한 문장만 입력하면 [START_HERE.md](../START_HERE.md) → 최신 **`lead/ugreen`** [실행 지침](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/START_HERE.md) → [현재 작업](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/LEAD_ACTIVE_WORK.md)을 조회하고, UGREEN **총괄 본인이 직접 개발·테스트·검수**한다. **아래 기능별 AI 작업자 3명/디스패처 문구는 폐기된 과거 이력이다.** `main`은 기본 진입·검증된 통합 기준이며 최신 진행은 lead 브랜치가 권위 있다.

# UGREEN — 2026 해커톤 AI 역할·브랜치·인수인계 진입점

> 2026-10-24 KST 최초 5브랜치·역할별 문서 직접 검증. 이 문서는 **main에만 있는 안내판**이다. 실제 작업 정보는 각 역할의 전담 브랜치에서 읽어야 한다. 채팅 간 자동 동기화는 없다.

| 역할 | 소유 브랜치 | 해당 역할 새 채팅 첫 문서 | 담당자 메시지 |
|---|---|---|---|
| 대회 총괄 | [`lead/ugreen`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/tree/lead/ugreen) | [총괄 HANDOFF](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/HANDOFF.md) | [전체 해커톤 총괄 보고](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/lead/ugreen/docs/roles/lead/TO_HACKATHON_LEAD.md) |
| 필수 파일 누락 | [`feature/missing-files`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/tree/feature/missing-files) | [작업자 HANDOFF](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/feature/missing-files/docs/roles/missing-files/HANDOFF.md) | [총괄에게 메시지](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/feature/missing-files/docs/roles/missing-files/TO_UGREEN_LEAD.md) |
| 중복·버전 충돌 | [`feature/version-conflicts`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/tree/feature/version-conflicts) | [작업자 HANDOFF](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/feature/version-conflicts/docs/roles/version-conflicts/HANDOFF.md) | [총괄에게 메시지](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/feature/version-conflicts/docs/roles/version-conflicts/TO_UGREEN_LEAD.md) |
| 개인정보 노출 점검 | [`feature/privacy`](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/tree/feature/privacy) | [작업자 HANDOFF](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/feature/privacy/docs/roles/privacy/HANDOFF.md) | [총괄에게 메시지](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/blob/feature/privacy/docs/roles/privacy/TO_UGREEN_LEAD.md) |

## 새로운 AI 채팅방에 전달하는 방법
- **대회 총괄:** `GitHub hibi89/hibi89-ugreen-nas-hackathon의 lead/ugreen 브랜치에서 docs/roles/lead/HANDOFF.md → STATUS.md → OPERATIONS.md → 루트 AGENTS.md/REQUIREMENTS.md → 최신 세 작업자 메시지함을 읽고, 원격 SHA·제품 현재 상태를 확인하라.`
- **기능 담당:** `GitHub hibi89/hibi89-ugreen-nas-hackathon의 feature/<본인 역할> 브랜치에서 docs/roles/<본인 역할>/HANDOFF.md → STATUS.md → OPERATIONS.md → 루트 AGENTS.md/REQUIREMENTS.md와 실제 소스를 읽고, 자기 브랜치에서만 작업하라.`
- **전체 해커톤 총괄:** [통합 상황실 START_HERE](https://github.com/hibi89/hackathon-command-center-2026/blob/main/START_HERE.md) → 이 대회 전담 총괄의 `TO_HACKATHON_LEAD.md` 읽기. 총괄의 코드 개발 책임을 침범하지 않는다.

## 운영 계약
1. 기능 담당자는 자기 브랜치에서만 실제 개발·테스트·문서 갱신. 보고는 각 `TO_UGREEN_LEAD.md`에 커밋한다.
2. 대회 총괄은 **새 지시 전에 세 메시지함 전수 확인**하고 `docs/roles/lead/MESSAGE_REVIEW.md`에 SHA·시간·판단 기록.
3. `main` 병합은 PR/테스트/검증 뒤 실시. 문서 초기화와 실서비스 작동은 별개.
4. 작업 종료 시 관련 `STATUS.md`, `HANDOFF.md`, 총괄 보고/메시지함을 함께 갱신하고 원격 SHA 확인. 빈 커밋·force push 금지.
5. 사용자의 확정 전 제품·API·데이터 계약은 **잠정**. 비용·결제·외부 데이터 전송·보안/접근 변경은 사용자 승인.
6. 저장소 **Public**. 토큰·.env·개인정보·고객 원본 금지. 제출 완료·실 API 정상·Production 동작의 미검증 성공 주장 금지.

## 현재 확인된 한계
- 브랜치 및 필수 문서 5/5 존재. 실제 제품 기능 0건, 외부 API/SDK 실검증 없음, CI/Production 미구축, 대회 제출 미완료.
- 신규 대회 총괄·기능 작업자 AI 채팅방 자체는 **아직 실제로 운영을 시작했다고 확인하지 않음**.
- 최신 원격 HEAD/CI는 **매 새 채팅 때 다시 조회**하라. 아래 SHA는 본 문서 작성 이전 관측값.
- `main`: `33e8ccf0226f6b108b6922f478004562cd3d53bf`; `lead/ugreen`: `8566f0c70d04d459ad71d088d58e59156387d0f4`.
- `feature/missing-files`: `fec871916e14aa6d56d8964cad912f2b253aa825`.
- `feature/version-conflicts`: `48ef0bbda3f347b43533ffab4642511444b1dac5`.
- `feature/privacy`: `b4a6dd098d06c41ea3f59ffe79494fa1e0a13d34`.
